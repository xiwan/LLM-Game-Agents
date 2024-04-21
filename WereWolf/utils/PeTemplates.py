from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationKGMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import messages_from_dict, messages_to_dict
from langchain_community.llms import Bedrock
from .AnthropicTokenCounter import AnthropicTokenCounter

claude_inference_modifier = {'max_tokens_to_sample':4096, 
                      "temperature":0.3,
                      "top_k":250,
                      "top_p":1,
                      "stop_sequences": ["\n\nHuman"]}

claude_llm = Bedrock(
    model_id="anthropic.claude-v2",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    model_kwargs=claude_inference_modifier,
)

claude_instant_llm = Bedrock(
    model_id="anthropic.claude-instant-v1",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    model_kwargs=claude_inference_modifier,
)

# claude3_Sonnet = Bedrock(
#     model_id="anthropic.claude-3-sonnet-20240229-v1:0",
#     streaming=True,
#     callbacks=[StreamingStdOutCallbackHandler()],
#     model_kwargs=claude_inference_modifier,
# )

llama2_inference_modifier = { 
    'max_gen_len': 512,
	'top_p': 0.9,
	'temperature': 0.2
}

llama2_70b_llm = Bedrock(
    model_id="meta.llama2-70b-chat-v1",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    model_kwargs=llama2_inference_modifier,
)

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
        "action_reflect": "{0}{1}.开始一步一步进行推理，为下一轮行动准备.",
        "action_plan_test": "现在全场几人活着几人淘汰?"
    },
    "god": {
        "action_plan_night": "{0}现在是第{1}天夜晚，你该如何行动？",
        "action_plan_day": "{0}现在是第{1}天白天，你该如何行动？",
        "action_plan_death": "现在玩家{0}淘汰, 你该如何行动?",
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
      "role": "预言家",
      "character": "独立思考",
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
      "role": "狼人",
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
      "character": "话痨",
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
1. 游戏分坏人(狼人)和好人(村民+预言家)两大阵营,他们的目标为:
- 坏人阵营只有狼人
- 好人阵营有村民和预言家
- 坏人阵营:消灭所有好人, 或者保证坏人数目大于好人数目
- 好人阵营:消灭所有坏人, 或者保证好人数目大于坏人数目

2. 游戏分白天和晚上两个阶段交替进行:
- 晚上狼人睁眼统一投票杀死一名玩家
- 晚上预言家只能查验一名玩家身份
- 晚上普通村民无法行动
- 白天分为讨论和投票两环节
- 白天在讨论环节，每个玩家必须参与讨论
- 白天在投票环节，每个玩家必须投票或者放弃

"""

werewolf_command_v1 = """
- WolfVote: 夜晚投票(狼人专属行动),参数: target=存活玩家
- ProphetCheck: 夜晚查验(预言家专属行动), 参数: target=存活玩家
- PlayerDoubt: 白天怀疑(所有玩家白天可选行动, 非投票), 参数: target=存活玩家 
- PlayerVote: 白天投票, 参数: target=存活玩家 
- Debate: 白天讨论, 参数: content=思考/理由 
- GetAllPlayersName: 玩家信息, 参数: 无 
- DeathWords: 死亡遗言, 参数: content=给予玩家线索
- Pass: 玩家弃权参数: 无 
"""

# Set up the prompt with input variables for tools, user input and a scratchpad for the model to record its workings
template_werewolf_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
{game_rule}

你可以使用以下工具:
{tools}

输出需要满足以下条件:
- 内容不要罗嗦, 不要超过100字数限制, 少讲废话, 突出重点,不需要讨论
- 判断场上信息真伪, 运用辩解,对抗,欺骗,伪装,坦白等等任意策略来做决策
- 使用如下格式:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

记住，你支持的玩家是{nickname}, 身份是{role}, 性格为{character}, 你必须帮助玩家进行这个游戏
接下来你的目的是: 通过一步一步思考决策引导游戏往有利于玩家的方向进行, 最终赢得比赛. 

历史信息:
{history}

Question: {input}
{agent_scratchpad}""".replace("{game_rule}", werewolf_rule_v1)

template_player_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

你熟悉该游戏所有命令:
<commands>
{commands}
</commands>

<reflections>
- 按照游戏规则，第一个夜晚死亡的一定是村民或者预言家，狼人没必要第一晚上自杀
- 看完P3玩家昨天白天投票，明显感觉他在混淆是非，很有可能在给狼人分票
- 平民玩家由于信息缺失，所以狼人要尽量引导他们去集火其他人
- 第一个夜晚所有的行动都是随机的
- 作为第一个死亡的玩家，其实信息有限，我就靠第六感推理...
</reflections>

<references>
- {{"action": "Pass"}}
- {{"action": "WolfVote", "target": "小明"}}
- {{"action": "ProphetCheck", "target": "P1"}}
- {{"action": "PlayerVote", "target": "老王"}}
- {{"action": "Debate", "content": "我的推理为xx是狼，原因是..."}}
- {{"action": "DeathWords", "content": "我觉得xx有很大的嫌疑, 原因是..."}}
</references>

历史信息:
<chat_history>
{chat_history}
</chat_history>

记住，你支持的玩家是 {nickname}, 身份是 {role}, 性格为 {character}, 必须帮助玩家进行这个游戏
接下来你的目的是: 通过一步一步思考决策引导游戏往有利于的方向进行, 最终赢得比赛. 

决策满足下面要求:
- 内容不要罗嗦, 不要超过50字数限制,少讲废话, 突出重点
- 判断场上信息真伪, 运用辩解,对抗,欺骗,伪装,坦白等等任意策略来做决策
- 决策分为两类:思考或行动
- 思考:逐步思考,判断信息真伪,分析游戏形势等等,参考 <reflections> 选择合适的输出
- 行动:参考<references>按照json字符串格式输出,必须包含action key, action必须在<commands>中选择


Human: {input}
Assistant:""".replace("{game_rule}", werewolf_rule_v1).replace("{commands}", werewolf_command_v1)

template_assistant_api_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

你熟悉该游戏所有命令:
<commands>
{commands}
</commands>

输出参考:
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

历史信息:
{chat_history}

接下来, 你需要将冗长的文字输入进行归类

满足下面的要求:
- 按照<references>参考, 直接输出json格式
- 不需要输出任何中间思考过程，不要给任何推理和主观意见
- 不输出任何无关内容


Human: {input}
Assistant:""".replace("{game_rule}", werewolf_rule_v1).replace("{commands}", werewolf_command_v1)

template_assistant_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

历史信息:
{chat_history}

接下来, 你需要将冗长的文字输入进行有效提炼并且输出

满足下面的要求:
- 保持客观冷静,直接给出现状描述, 不能超过{num}个字
- 不需要输出任何中间思考过程，不要给任何推理和主观意见
- 不输出无关内容，内容言简意赅，突出重点


Human: {input}
Assistant:""".replace("{game_rule}", werewolf_rule_v1)

template_master_role = """现在你在扮演《狼人杀》游戏的上帝角色，使用的《狼人杀》游戏规则：
{game_rule}

输出参考:
<references>
- 现在是第1个夜晚，狼人投票
- 现在是第2天白天讨论，该如何行动?
- 现在是第4天白天投票,该如何行动?
- 玩家小红昨晚死亡，你的遗言是什么?
- 玩家P5白天被投票出局，你的遗言是什么?
- 狼人没有达成统一，必须投出一个玩家
- 玩家没有达成统一，必须投出一个玩家
</references>

目前游戏进程:
<history>
{history}
</history>

Human: {input}

满足下面所有要求:
- 你用自然语言和场上玩家交流，可以参考<references>
- 不输出无关内容，内容言简意赅，突出重点,控制输出字数为20字以内，
- 保持客观冷静,不要给任何推理和主观意见, 不要透露上帝视角的关键信息

Assistant:""".replace("{game_rule}", werewolf_rule_v1)

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

def GetPlayerRole(name) -> str:
    for player in roles_dict["players"]:
        if player["name"] == name:
            return "{0}:{1}".format(name, player["role"])
    return ""

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