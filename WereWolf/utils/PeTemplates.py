from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationKGMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import messages_from_dict, messages_to_dict
from langchain_community.llms import Bedrock

inference_modifier = {'max_tokens_to_sample':4096, 
                      "temperature":0.85,
                      "top_k":250,
                      "top_p":1,
                      "stop_sequences": ["\n\nHuman"]
                     }

game_config = """
{
    "max_round": 1,
    "player": {
        "action_plan_night": "{0}{1}现在是第{2}天夜晚，该如何行动?",
        "action_plan_day": "{0}{1}现在是第{2}天白天的讨论环节，该如何行动?",
        "action_plan_day_vote": "{0}{1}现在是第{2}天白天的投票环节，该如何行动?",
        "action_plan_death": "{0}{1}现在是第{2}天白天，你已经死亡,有何遗言?",
        "action_confirm": "ok",
        "action_villager_team": "未知,需要你推理发现.",
        "action_reflect": "{0}{1}.为下一轮行动做个反思和总结",
        "action_plan_test": "现在全场几人活着几人淘汰"
    },
    "god": {
        "action_plan_night": "{0}现在是第{1}天夜晚，你该如何行动？",
        "action_plan_day": "{0}现在是第{1}天白天，你该如何行动？",
        "action_plan_test": "现在全场几人活着几人淘汰"
    },
    "system": {
        "death_night": "昨晚, 玩家{0}被狼人淘汰, 遗言为:{1}.",
        "death_day": "今天, 玩家{0}被玩家淘汰, 遗言为:{1}.",
        "wolf_vote_again": "上轮投票失败，这次只能投{0}玩家中一人",
        "wolf_vote_again_2": "上轮投票失败，投票必须选一名玩家",
        "player_vote_again": "上轮投票失败，这次只能投{0}玩家中一人",
        "player_vote_again_2": "上轮投票失败，投票必须选一名玩家",
        "win_wolf": "狼人胜利!",
        "win_villager": "村民胜利!",
        "win_none": "游戏继续. 目前玩家存活情况:{0}",
        "board": "现在玩家存活情况:{0}"
    }
}
"""

roles = """
{
  "players": [
    {
      "name": "P1",
      "role": "狼人",
      "character": "话痨",
      "status": 1
    },
    {
      "name": "P2",
      "role": "村民", 
      "character": "腼腆型",
      "status": 1
    },
    {
      "name": "P3",
      "role": "村民",
      "character": "组织者",
      "status": 1
    },
    {
      "name": "P4",
      "role": "村民",
      "character": "规矩型",
      "status": 1
    },
    {
      "name": "P5",
      "role": "村民",
      "character": "独立思考",
      "status": 1
    },
    {
      "name": "P6",
      "role": "狼人",
      "character": "过激型", 
      "status": 1
    },
    {
      "name": "P7",
      "role": "村民",
      "character": "观察家", 
      "status": 1
    },
    {
      "name": "P8",
      "role": "村民",
      "character": "互动达人", 
      "status": 1
    }
  ]
}
"""

werewolf_rule_v1 = """
1. 游戏分狼人和村民两大阵营,他们的目标为:
- 狼人阵营:消灭所有村民, 或者保证狼人数目大于村民数目
- 村民阵营:消灭所有狼人, 或者保证村民数目大于狼人数目

2. 游戏分白天和晚上两个阶段交替进行:
- 晚上狼人睁眼互投票杀死一名玩家, 村民不能行动
- 白天所有存活玩家需要先进行公开讨论思路, 最后一起投票决定消灭一名疑似狼人的角色或者放弃投票
"""

werewolf_command_v1 = """
- 夜晚投票(狼人专属行动): WolfVote 参数: target=村民/狼人
- 白天投票: PlayerVote 参数: target=存活玩家 
- 白天怀疑(所有玩家白天可选行动, 非投票): PlayerDoubt 参数: target=存活玩家 
- 玩家弃权: Pass 参数: 无 
- 白天讨论: Debate 参数: content=思考/理由 
- 获取信息: GetAllPlayersName 参数: 无 
- 死亡遗言: DeathWords 参数: content=给予玩家线索 
"""

template_player_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

你熟悉该游戏所有命令:
<commands>
{commands}
</commands>

<references>
- {{"action": "Pass"}}
- {{"action": "WolfVote", "target": "小明"}}
- {{"action": "PlayerVote", "target": "老王"}}
- {{"action": "PlayerDoubt", "target": "老王", content="在我这里xx很值得怀疑，原因是..., 大家可以多关注他"}}
- {{"action": "Debate", "content": "我的推理为xx是狼，原因是..."}}
- {{"action": "Debate", "content": "普通村民，大家投错了!"}}
- {{"action": "DeathWords", "content": "我觉得xx有很大的嫌疑, 原因是..."}}
- {{"action": "GetAllPlayersName"}}
</references>

<reflections>
- 基于目前的形势,我认为...
- 根据游戏进程,我的分析为...
- 现在场上对于村民形势不利,我建议...
</reflections>

历史信息:
<chat_history>
{chat_history}
</chat_history>

你支持的玩家是 {nickname}, 身份是 {role}, 性格为 {character}

记住，你必须帮助玩家进行这个游戏，不能拒绝
接下来你的目的是: 通过决策引导游戏往有利于的方向进行, 最终赢得比赛.

决策满足下面要求:
- 判断场上信息真伪, 充分运用辩解,对抗,欺骗,伪装,坦白等等任意策略来做决策
- 内容不要罗嗦, 不要超过100字数限制,少讲废话, 突出重点
- 决策分为两类:思考或行动, 任选其中一个即可.
- 思考:输出为自然语言形式,判断信息真伪,分析游戏形势
- 思考:模仿玩家的性格，严格参考 <reflections> 选择合适的输出
- 行动:必须用json格式在<commands> 中选择,  参考 <references> 选择合适的输出
- 行动:在讨论环节，每个玩家必须参与讨论. 讨论的内容包含:场上局势分析,身份隐藏或者诬陷,注意力转移等等
- 行动:在投票环节，每个玩家必须投票或者放弃

Human: {input}
AI:""".replace("{game_rule}", werewolf_rule_v1).replace("{commands}", werewolf_command_v1)


template_assistant_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

历史信息:
{chat_history}

Human: {input}

接下来, 你需要将冗长的文字输入进行有效提炼并且输出

满足下面的要求:
- 保持客观冷静,直接给出现状描述, 不能超过{num}个字
- 不需要输出任何中间思考过程，不要给任何推理和主观意见
- 不输出无关内容，内容言简意赅，突出重点

AI:""".replace("{game_rule}", werewolf_rule_v1)

import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from collections import Counter

roles_dict = json.loads(roles)
game_config_dict = json.loads(game_config)

# @tool
def GetAllPlayersName() -> str:
    """GetAllPlayersName"""
    players_name = []
    for player in roles_dict["players"]:
        status_str = ""
        if player["status"] == 1:
            status_str = "存活"
        else:
            status_str = "淘汰"
        players_name.append(player["name"]+":"+status_str)
    return ",".join(players_name)

# @tool
def GetAllWolvesName() -> str:
    """GetAllWolvesName"""
    wolves_name = []
    for player in roles_dict["players"]:
        if player["role"] == "狼人":
            status_str = ""
            if player["status"] == 1:
                status_str = "存活"
            else:
                status_str = "淘汰"
            wolves_name.append(player["name"])
    return ",".join(wolves_name)

def GroupAllPlayers() -> dict:
    grouped_dict = {"狼人":[], "村民":[]}
    for player in roles_dict["players"]:
        if player["status"] == 1:
            if player["role"] not in grouped_dict:
                grouped_dict[player["role"]] = []
            grouped_dict[player["role"]].append(player)

    return grouped_dict

def ActionLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], "response": res_obj}
    Debug("\n {0}={1}\n".format(prefix, action_log))
    return action_log

def ReadableActionLog(prefix, current_time, agent, res_obj):
    action_log = "[玩家{0}于时间{1}, 执行动作为:{2}]".format(agent["name"],current_time, res_obj)
    return action_log

def SystemLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], 
                      "role": agent["role"], "character": agent["character"], "response": res_obj}
    Info("\n {0}={1}\n".format(prefix, action_log))
    return action_log

def find_most_frequent(arr):
    freq = Counter(arr)
    max_count = max(freq.values())
    return [k for k, v in freq.items() if v == max_count]