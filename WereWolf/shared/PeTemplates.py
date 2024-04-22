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

def GetPartySize() -> str:
    grouped_dict = GroupAllPlayers()
    return "{0}狼人,{1}村民,{2}预言家,{3}女巫".format(len(grouped_dict["狼人"]),
                                                len(grouped_dict["村民"]),
                                                len(grouped_dict["预言家"]),
                                                len(grouped_dict["女巫"]))

def GetPlayer(players, role):
    for player in players:
        if player.GetRole() == role:
            return player
    return None

def GetPlayerRole(name) -> str:
    for player in roles_dict["players"]:
        if player["name"] == name:
            return "{0}:{1}".format(name, player["role"])
    return ""

def GetPlayerInfo() -> str:
    player_info = []
    for player in roles_dict["players"]:
        tmp_player = {}
        tmp_player["id"] = player["id"]
        tmp_player["name"] = player["name"]
        tmp_player["role"] = player["role"]
        tmp_player["character"] = player["character"]
        tmp_player["status"] = player["status"]
        player_info.append(tmp_player)
    return player_info

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

def GroupAlivePlayers() -> dict:
    grouped_dict = {"狼人":[], "村民":[], "预言家":[], "女巫":[]}
    for player in roles_dict["players"]:
        if player["status"] == 1:
            if player["role"] not in grouped_dict:
                grouped_dict[player["role"]] = []
            grouped_dict[player["role"]].append(player)
    return grouped_dict

def GroupAllPlayers() -> dict:
    grouped_dict = {"狼人":[], "村民":[], "预言家":[], "女巫":[]}
    for player in roles_dict["players"]:
        if player["role"] not in grouped_dict:
            grouped_dict[player["role"]] = []
        grouped_dict[player["role"]].append(player)
    return grouped_dict
    
def ActionLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], "response": res_obj}
    logger.debug("\n ActionLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def ReadableActionLog(prefix, current_time, name, res_obj):
    action_log = "时间:{0}, 玩家:{1},动作:{2}".format(current_time, name, res_obj)
    logger.debug("\n ReadableActionLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def SystemLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], 
                      "role": agent["role"], "character": agent["character"], "response": res_obj}
    logger.info("\n SystemLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def ParseJson(text):
    try:
        # 使用正则表达式查找 {} 之间的内容
        json_pattern = re.compile( r'{[\s\S]*?}') 
        json_strings = re.findall(json_pattern, text)
        return json_strings
    except Error:
        logger.exception("Cannot parse json")
    return None

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
        logger.exception("Can not retrive tools")
        raise

werewolf_rule_v1 = LoadPrompt("werewolf_rule.txt")
werewolf_command_v1 = LoadPrompt("werewolf_command.txt")

wolf_command = RetriveTools(werewolf_command_v1, "wolf").rstrip("\n")
prophet_command = RetriveTools(werewolf_command_v1, "prophet").rstrip("\n")
witch_command = RetriveTools(werewolf_command_v1, "witch").rstrip("\n")
palyer_command = RetriveTools(werewolf_command_v1, "player").rstrip("\n")

wolf_tools = wolf_command + palyer_command
prophet_tools = prophet_command + palyer_command
witch_tools = witch_command + palyer_command
player_tools = palyer_command

all_tools = wolf_command+prophet_command+witch_command+palyer_command

template_wolf_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", wolf_tools)
template_prophet_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", prophet_tools)
template_witch_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", witch_tools)
template_player_role = LoadPrompt("template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", player_tools)
template_assistant_role = LoadPrompt("template_assistant_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", all_tools)

roles = LoadConfig("roles.txt")
game_config = LoadConfig("game_config.txt")

roles_dict = json.loads(roles)
game_config_dict = json.loads(game_config)

def ShufflePlayers():
    roles = [player['role'] for player in roles_dict['players']]
    # 打乱角色列表
    random.shuffle(roles)
    for i, player in enumerate(roles_dict['players']):
        player['role'] = roles[i]
    #print(roles_dict)

def LoadPlayerPrompts() -> str:
    for player in roles_dict["players"]:
        if player["role"] == "狼人":
            player["prompt"] = template_wolf_role
        elif player["role"] == "村民":
            player["prompt"] = template_player_role
        elif player["role"] == "预言家":
            player["prompt"] = template_prophet_role
        elif player["role"] == "女巫":
            player["prompt"] = template_witch_role
        else:
            player["prompt"] = ""
            pass
        # print(player["prompt"])
        
    
def SortedPlayersInNight(players):
    # 定义角色优先级字典
    role_priorities = {
        "狼人": 1,
        "预言家": 2,
        "女巫": 3,
        "村民": 4
    }
    # 根据角色优先级对玩家列表进行排序
    sorted_players = sorted(players, key=lambda player: role_priorities.get(player.GetRole(), 5))

    return sorted_players
