from . import *

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

template_player_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

你熟悉该游戏所有命令:
<commands>
{commands}
</commands>

<references>
- {"action": "Pass"}
- {"action": "WolfVote", "target": "小明"}
- {"action": "ProphetCheck", "target": "P1"}
- {"action": "PlayerVote", "target": "老王"}
- {"action": "Debate", "content": "我的推理为xx是狼，原因是..."}
- {"action": "DeathWords", "content": "我觉得xx有很大的嫌疑, 原因是..."}
</references>

历史信息:
<chat_history>
{chat_history}
</chat_history>

记住，你支持的玩家是"{nickname}", 身份是"{role}", 性格为"{character}", 必须帮助玩家进行这个游戏
接下来你的目的是: 通过一步一步思考决策引导游戏往有利于的方向进行, 最终赢得比赛. 

使用如下格式:
Thought: 逐步思考,判断信息真伪, 分析游戏形势等等, 运用辩解,对抗,欺骗,伪装,坦白等等任意策略来做决策. 注意不要超过100字数限制, 少讲废话, 突出重点
Action: 必须在<commands>中选择
Action Input: the input to the action
Final Answer: 参考<references>, 按照json字符串格式输出

{input}:""".replace("{game_rule}", werewolf_rule_v1).replace("{commands}", werewolf_command_v1)

template_assistant_role = """你是资深的社交游戏玩家, 熟悉《狼人杀》游戏规则:
<game_rules>
{game_rule}
</game_rules>

接下来, 你需要将冗长的文字输入进行有效提炼并且输出

满足下面的要求:
- 保持客观冷静,直接给出现状描述, 不能超过{num}个字
- 不需要输出任何中间思考过程，不要给任何推理和主观意见
- 不输出无关内容，内容言简意赅，突出重点

{input}:""".replace("{game_rule}", werewolf_rule_v1)

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
    logger.debug("\n {0}={1}\n".format(prefix, action_log))
    return action_log

def ReadableActionLog(prefix, current_time, agent, res_obj):
    action_log = "[玩家{0}于时间{1}, 执行动作为:{2}]".format(agent["name"],current_time, res_obj)
    return action_log

def SystemLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], 
                      "role": agent["role"], "character": agent["character"], "response": res_obj}
    logger.info("\n {0}={1}\n".format(prefix, action_log))
    return action_log

def ParseJson(text):
    # 使用正则表达式查找 {} 之间的内容
    json_pattern = re.compile( r'{[\s\S]*?}') 
    json_strings = re.findall(json_pattern, text)
    return json_strings

def find_most_frequent(arr):
    freq = Counter(arr)
    max_count = max(freq.values())
    return [k for k, v in freq.items() if v == max_count]