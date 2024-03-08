from . import *

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

def FindMostFrequent(arr):
    freq = Counter(arr)
    max_count = max(freq.values())
    return [k for k, v in freq.items() if v == max_count]

def LoadPrompt(promptfile: str) -> str:
    with open("./shared/prompts/{}".format(promptfile), 'r') as f:
        content = f.read()
        return content.strip()
    
def LoadConfig(configfile: str) -> str:
    with open("./shared/configs/{}".format(configfile), 'r') as f:
        content = f.read()
        return content.strip()

def RetriveTools(text: str, tag_name: str) -> str:
    try:
        pattern = r'<%s>(.*?)</%s>' % (tag_name, tag_name)
        actions = re.findall(pattern, text, re.DOTALL)
        return actions[0]
    except Error:
        logger.exception("Can't not retrive tools")
        raise

werewolf_rule_v1 = LoadPrompt("werewolf_rule.txt")
werewolf_command_v1 = LoadPrompt("werewolf_command.txt")

wolf_command = RetriveTools(werewolf_command_v1, "wolf")
prophet_command = RetriveTools(werewolf_command_v1, "prophet")
palyer_command = RetriveTools(werewolf_command_v1, "player")

wolf_tools = wolf_command + palyer_command
prophet_tools = prophet_command + palyer_command
player_tools = palyer_command

template_wolf_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", wolf_tools)
template_prophet_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", prophet_tools)
template_player_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", player_tools)

template_assistant_role = LoadPrompt("template_assistant_role.txt").replace("{game_rule}", werewolf_rule_v1)

roles = LoadConfig("roles.txt")
game_config = LoadConfig("game_config.txt")

roles_dict = json.loads(roles)
game_config_dict = json.loads(game_config)

def LoadPlayerPrompts() -> str:
    for player in roles_dict["players"]:
        if player["role"] == "狼人":
            player["prompt"] = template_wolf_role
        elif player["role"] == "村民":
            player["prompt"] = template_player_role
        elif player["role"] == "预言家":
            player["prompt"] = template_prophet_role
        else:
            player["prompt"] = ""
            pass