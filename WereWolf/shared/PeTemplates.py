from . import *

def GetPlayer(players, role):
    for player in players:
        if player.GetRole() == role:
            return player
    return None

def GetPlayerRole(name, roles_dict=[], lang="cn") -> str:
    for player in roles_dict["players"]:
        if player["name"] == name:
            return "{0}:{1}".format(name, player["role"])
    return ""

def GetPlayerInfo(roles_dict=[], lang="cn") -> str:
    player_info = []
    for player in roles_dict["players"]:
        tmp_player = {}
        tmp_player["id"] = player["id"]
        tmp_player["name"] = player["name"]
        tmp_player["role"] = player["role"]
        tmp_player["character"] = player["character"]
        tmp_player["status"] = player["status"]
        tmp_player["gender"] = player["gender"]
        player_info.append(tmp_player)
    return player_info
    
# @tool
def GetAllPlayersName(roles_dict=[], lang="cn") -> str:
    """GetAllPlayersName"""
    players_name = []
    #print(lang)
    for player in roles_dict["players"]:
        status_str = ""
        if player["status"] == 1:
            status_str = mappings["status_alive"].get(lang)
        else:
            status_str = mappings["status_eliminated"].get(lang)
        players_name.append(player["name"]+":"+status_str)
    return ",".join(players_name)

def GetPartySize(roles_dict=[], lang="cn") -> str:
    grouped_dict = GroupAllPlayers(roles_dict, lang)

    partyInfo = []
    partyInfo.append("{0}{1} ".format(len(grouped_dict[mappings["wolf"].get(lang)]), mappings["wolf"].get(lang)))
    partyInfo.append("{0}{1} ".format(len(grouped_dict[mappings["villager"].get(lang)]), mappings["villager"].get(lang)))
    partyInfo.append("{0}{1} ".format(len(grouped_dict[mappings["prophet"].get(lang)]), mappings["prophet"].get(lang)))
    partyInfo.append("{0}{1} ".format(len(grouped_dict[mappings["witch"].get(lang)]), mappings["witch"].get(lang)))
    #print(partyInfo)
    return ",".join(partyInfo)
    # return "{0}狼人,{1}村民,{2}预言家,{3}女巫".format(len(grouped_dict["狼人"]),
    #                                             len(grouped_dict["村民"]),
    #                                             len(grouped_dict["预言家"]),
    #                                             len(grouped_dict["女巫"]))

# @tool
def GetAllWolvesName(roles_dict=[], lang="cn") -> str:
    """GetAllWolvesName"""
    wolves_name = []
    for player in roles_dict["players"]:
        if player["role"] == mappings["wolf"].get(lang):
            status_str = ""
            if player["status"] == 1:
                status_str = mappings["status_alive"].get(lang)
            else:
                status_str = mappings["status_eliminated"].get(lang)
            wolves_name.append(player["name"])
    return ",".join(wolves_name)

def GroupAlivePlayers(roles_dict=[], lang="cn") -> dict:

    grouped_dict = {}
    grouped_dict[mappings["wolf"].get(lang)] = []
    grouped_dict[mappings["prophet"].get(lang)] = []
    grouped_dict[mappings["witch"].get(lang)] = []
    grouped_dict[mappings["villager"].get(lang)] = []
    
    # grouped_dict = {"狼人":[], "村民":[], "预言家":[], "女巫":[]}
    for player in roles_dict["players"]:
        if player["status"] == 1:
            if player["role"] not in grouped_dict:
                grouped_dict[player["role"]] = []
            grouped_dict[player["role"]].append(player)
    return grouped_dict

def GroupAllPlayers(roles_dict=[], lang="cn") -> dict:
    grouped_dict = {}
    grouped_dict[mappings["wolf"].get(lang)] = []
    grouped_dict[mappings["prophet"].get(lang)] = []
    grouped_dict[mappings["witch"].get(lang)] = []
    grouped_dict[mappings["villager"].get(lang)] = []
    
    # grouped_dict = {"狼人":[], "村民":[], "预言家":[], "女巫":[]}
    for player in roles_dict["players"]:
        if player["role"] not in grouped_dict:
            grouped_dict[player["role"]] = []
        grouped_dict[player["role"]].append(player)
        
    return grouped_dict
    
def ActionLog(prefix, current_time, agent, res_obj):
    print(res_obj)
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], "response": res_obj}
    logger.debug("\n ActionLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def ReadableActionLog(prefix, current_time, name, res_obj):
    action_log = "Time:{0}, Player:{1}, Action:{2}".format(current_time, name, res_obj)
    logger.debug("\n ReadableActionLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def SystemLog(prefix, current_time, agent, res_obj):
    action_log = {"time": current_time, "player": agent["name"], "status": agent['status'], 
                      "role": agent["role"], "character": agent["character"], "response": res_obj}
    logger.info("\n SystemLog: {0}={1}\n".format(prefix, action_log))
    return action_log

def ConvertToJson(data):
    try:
        if isinstance(data, str):
            return json.loads(data)
        else:
            return data
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return data
    
def ParseJson(text):
    try:
        # 使用正则表达式查找 {} 之间的内容
        json_pattern = re.compile( r'{[\s\S]*?}') 
        json_strings = re.findall(json_pattern, text)
        return json_strings
    except Error:
        logger.exception("Cannot parse json")
    return None

def IsValidJson(json_str):
    try:
        # print(json_str)
        json.loads(json_str)
    except ValueError as e:
        return False
    return True

def EqualIgnoreCase(str1, str2):
    return str1.lower().strip() == str2.lower().strip()

def FindMostFrequent(arr):
    freq = Counter(arr)
    max_count = max(freq.values())
    return [k for k, v in freq.items() if v == max_count]

def LoadPrompt(lang: str, promptfile: str) -> str:
    with open("./shared/prompts/{}/{}".format(lang, promptfile), 'r') as f:
        content = f.read()
        return content.strip()
    
def LoadConfig(lang: str, configfile: str) -> str:
    with open("./shared/configs/{}/{}".format(lang, configfile), 'r') as f:
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
    
def InitGlobals(lang="cn"):
    game_config = LoadConfig(lang, "game_config.txt")
    game_config_dict = json.loads(game_config)

    roles = LoadConfig(lang, "roles.txt")
    roles_dict = json.loads(roles)

    for player in roles_dict["players"]:
        player["gender"] = random.choice([0,1])
        
    return (roles_dict, game_config_dict) 
    
def ShufflePlayers(roles_dict=[]):
    roles = [player['role'] for player in roles_dict['players']]
    # 打乱角色列表
    random.shuffle(roles)
    for i, player in enumerate(roles_dict['players']):
        player['role'] = roles[i]
    # print(roles_dict)

def LoadPlayerPrompts(lang="cn", roles_dict=[]) -> str:
    werewolf_rule_v1 = LoadPrompt(lang, "werewolf_rule.txt")
    werewolf_command_v1 = LoadPrompt(lang, "werewolf_command.txt")

    wolf_command = RetriveTools(werewolf_command_v1, "wolf").rstrip("\n")
    prophet_command = RetriveTools(werewolf_command_v1, "prophet").rstrip("\n")
    witch_command = RetriveTools(werewolf_command_v1, "witch").rstrip("\n")
    palyer_command = RetriveTools(werewolf_command_v1, "player").rstrip("\n")

    wolf_tools = wolf_command + palyer_command
    prophet_tools = prophet_command + palyer_command
    witch_tools = witch_command + palyer_command
    player_tools = palyer_command

    all_tools = wolf_command+prophet_command+witch_command+palyer_command

    template_wolf_role = LoadPrompt(lang, "template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", wolf_tools)
    template_prophet_role = LoadPrompt(lang, "template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", prophet_tools)
    template_witch_role = LoadPrompt(lang, "template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", witch_tools)
    template_player_role = LoadPrompt(lang, "template_player_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", player_tools)

    template_assistant_summarize_role = LoadPrompt(lang, "template_assistant_summarize_role.txt").replace("{game_rule}", werewolf_rule_v1).replace("{commands}", all_tools)
    template_assistant_recommend_role = LoadPrompt(lang, "template_assistant_recommend_role.txt").replace("{game_rule}", werewolf_rule_v1)

    for player in roles_dict["players"]:
        # player["reflect_prompt"] = template_assistant_recommend_role
        player["summary_prompt"] = template_assistant_summarize_role
        if EqualIgnoreCase(player["role"], mappings["wolf"].get(lang)):
            player["action_prompt"] = template_wolf_role
            player["reflect_prompt"] = template_assistant_recommend_role.replace("{commands}", wolf_tools)
        elif EqualIgnoreCase(player["role"], mappings["villager"].get(lang)):
            player["action_prompt"] = template_player_role
            player["reflect_prompt"] = template_assistant_recommend_role.replace("{commands}", player_tools)
        elif EqualIgnoreCase(player["role"], mappings["prophet"].get(lang)):
            player["action_prompt"] = template_prophet_role
            player["reflect_prompt"] = template_assistant_recommend_role.replace("{commands}", prophet_tools)
        elif EqualIgnoreCase(player["role"], mappings["witch"].get(lang)):
            player["action_prompt"] = template_witch_role
            player["reflect_prompt"] = template_assistant_recommend_role.replace("{commands}", witch_tools)
        else:
            player["action_prompt"] = ""
            player["reflect_prompt"] = ""
            pass
        
    
def SortedPlayersInNight(players, lang="cn"):
    # 定义角色优先级字典
    role_priorities = {}
    role_priorities[mappings["wolf"].get(lang)] = 1
    role_priorities[mappings["prophet"].get(lang)] = 2
    role_priorities[mappings["witch"].get(lang)] = 3
    role_priorities[mappings["villager"].get(lang)] = 4

    # 根据角色优先级对玩家列表进行排序
    return sorted(players, key=lambda player: role_priorities.get(player.GetRole(), 5))

#roles_dict,game_config_dict = InitGlobals()
