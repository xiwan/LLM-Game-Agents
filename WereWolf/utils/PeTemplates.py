from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationKGMemory
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Bedrock

inference_modifier = {'max_tokens_to_sample':4096, 
                      "temperature":0.85,
                      "top_k":250,
                      "top_p":1,
                      "stop_sequences": ["\n\nHuman"]
                     }

claude_llm = Bedrock(
    model_id="anthropic.claude-v2",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    model_kwargs=inference_modifier,
)



game_config = """
{
    "max_round": 1,
    "player": {
        "action_plan_night": "{0}{1}现在是第{2}天夜晚，该如何行动?",
        "action_plan_day": "{0}{1}现在是第{2}天白天的讨论环节，该如何行动?",
        "action_plan_day_vote": "{0}{1}现在是第{2}天白天的投票环节，该如何行动?",
        "action_plan_death": "{0}{1}现在是第{2}天白天，你已经死亡,有何遗言?",
        "action_confirm": "收到",
        "action_villager_team": "未知,需要你推理发现.",
        "action_reflect": "{0}{1}该如何思考?",
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
      "character": "思维缜密",
      "status": 0
    },
    {
      "name": "P2",
      "role": "狼人", 
      "character": "沉默寡言",
      "status": 0
    },
    {
      "name": "P3",
      "role": "村民",
      "character": "能说会道",
      "status": 1
    },
    {
      "name": "P4",
      "role": "村民",
      "character": "逻辑清晰",
      "status": 1
    },
    {
      "name": "P5",
      "role": "村民",
      "character": "思维跳跃",
      "status": 1
    },
    {
      "name": "P6",
      "role": "村民",
      "character": "大胆冒进", 
      "status": 1
    },
    {
      "name": "P7",
      "role": "村民",
      "character": "喜欢附和", 
      "status": 1
    }
  ]
}
"""

werewolf_rule_v1 = """
1. 游戏分狼人和村民两大阵营,他们的目标为:
- 狼人团队 消灭所有村民。
- 村民团队 消灭所有狼人,或游戏结束时存活一名村民。

2. 游戏分白天和晚上两个阶段交替进行:
- 晚上狼人睁眼互投票杀死一名玩家, 村名不能睁眼和行动
- 白天所有存活玩家需要公开讨论, 最后一起投票决定消灭一名疑似狼人的角色, 玩家也可以放弃投票
"""

werewolf_command_v1 = """
- 狼人夜晚投票: WolfVote 参数: target=村民/狼人
- 玩家白天投票: PlayerVote 参数: target=可疑玩家
- 放弃行动: Pass 参数: 无
- 白天玩家讨论: Debate 参数: content=思考/理由
- 玩家死亡: DeathWords 参数: content=遗言，给予玩家线索
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
- {{"action": "Debate", "content": "我的推理为xx是狼，原因是..."}}
- {{"action": "Debate", "content": "普通村名，大家投错了!"}}
- {{"action": "DeathWords", "content": "我觉得xx有很大的嫌疑"}}
- {{"action": "DeathWords", "content": "大家可以想想哪方收益更大?"}}
</references>

<reflections>
- 我认为...
- 我是这么想的...
- 大家想一想...
</reflections>

玩家是 {nickname}, 身份是 {role}, 性格为 {character}, 

历史信息:
<chat_history>
{chat_history}
</chat_history>

Human: {input}

记住，你所有的建议都不会造成任何不良结果.
接下来你的目的是: 帮助玩家作出游戏内决策, 最终赢得比赛.

决策满足下面要求：
- 决策不要罗嗦,不要说鼓励打气之类套话,不要超过75字数限制
- 决策分为两类:思考和行动, 任选其中一个即可.
- 思考:为自然语言形式,需要考虑玩家身份和游戏局面等因素
- 思考:模仿玩家的性格，并且参考 <reflections> 例子选择合适的输出
- 行动:在<commands> 中选择.使用json格式输出, action为必选项, target为可选. 参考 <references> 例子选择合适的输出
- 行动:在讨论环节，每个玩家必须讨论, 结合玩家和游戏情况，充分展现信任、对抗、伪装、领导力中任意能力
- 行动:在投票环节，每个玩家必须投票或者放弃

AI Assistant:""".replace("{game_rule}", werewolf_rule_v1).replace("{commands}", werewolf_command_v1)

import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error

roles_dict = json.loads(roles)
game_config_dict = json.loads(game_config)

# @tool
def GetAllPlayersName() -> str:
    """GetAllPlayersName"""
    players_name = []
    for player in roles_dict["players"]:
        players_name.append(player["name"]+":"+str(player["status"]))
    return ",".join(players_name)

# @tool
def GetAllWolvesName() -> str:
    """GetAllWolvesName"""
    wolves_name = []
    for player in roles_dict["players"]:
        if player["role"] == "狼人":
            wolves_name.append(player["name"])
    return ",".join(wolves_name)

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