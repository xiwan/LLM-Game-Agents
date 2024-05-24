from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .GamePlayerWitch import GamePlayerWitch
from .GamePlayerWolf import GamePlayerWolf
from .GamePlayerProphet import GamePlayerProphet
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate
from enum import Enum

class GameStage(Enum):
    Unknown = 0
    NightWolf = 1
    NightPropht = 2
    NightWitch = 3
    NightAction = 4
    DeathWords = 5
    DayDebate = 6
    DayVote = 7
    Assistant = 8

@singleton
class GameMaster(object):
    
    def __init__(self, num=10, queueSize=10, quick=False, lang="cn") -> None:
        self.quick = quick
        self.queueSize = queueSize
        self.lang = lang
        LANG = self.lang
        self.num = num
        self._resetGlobal()
 
        # assistant agent
        # _template_assistant_recommend_role = template_assistant_recommend_role.replace("{num}", "144")
        # self.assistant = GameAssistant(_template_assistant_recommend_role, GM)
        
        pass
        
        
    def _resetGlobal(self):
        self.roles_dict=[]
        self.game_config_dict=[]
        self.roles_dict,self.game_config_dict = InitGlobals(self.lang)
        
        self.game_config_dict["max_round"] = self.num
        
        self.run = True
        self.exit_flag = False
        self.inGame = False
        self.round = 0
        self.isDay = False
        self.stage = GameStage.Unknown.value
        self.current_time = ""
        self.game_memory_queue = queue.Queue(maxsize=self.queueSize)
        self.game_output_queue = queue.Queue(maxsize=self.queueSize)
        
        # memory log array
        self.game_public_log = []
        self.game_wolf_vote_log = []
        self.game_player_vote_log = []
        self.game_prophet_check_log = []
        self.game_witch_potion_log = []
        self.game_player_action_log = []
        self.game_player_death_log = []
        self.game_system_log = []

        self.player_agents = []
        self.winner = 0  # 0: 继续 1: 好人 2:坏人
        
        self.wolfvotes = []
        self.palyervotes = []
        self.input_tokens = 0
        self.output_tokens = 0
        self.god_instruct = ""
        # self.quick = False
        pass
    
    def _current_time(self, i):
        self.round = i
        if self.isDay:
            self.current_time = "DAY-{0}".format(self.round)
        else:
            self.current_time = "NIGHT-{0}".format(self.round)
        return self.current_time
    
    def _reviveRoles(self):
        for player in self.roles_dict["players"]:
            player["status"] = 1
            
    def _checkWinner(self) -> str:
        """CheckWinner"""
        grouped_dict = GroupAlivePlayers(self.roles_dict, self.lang)
        bad_party_size = len(grouped_dict[self.Lang("wolf")])
        good_party_size = len(grouped_dict[self.Lang("villager")])+len(grouped_dict[self.Lang("prophet")])+len(grouped_dict[self.Lang("witch")])
        
        message = self.Lang("MasterCheckWinner").format(self.current_time, str(bad_party_size), str(good_party_size))

        if bad_party_size == 0 and good_party_size > 0:
            return 1
        if bad_party_size > 0 and good_party_size <= bad_party_size:
            return 2 
        return 0
            
    ## setup Players
    def _setupPlayers(self):
        ShufflePlayers(self.roles_dict)
        LoadPlayerPrompts(self.lang, self.roles_dict)
        # cache the player agents
        for player in self.roles_dict["players"]:
            _palyer = None
            if EqualIgnoreCase(player["role"], self.Lang("witch")):
                _player = GamePlayerWitch(player, self)
            elif EqualIgnoreCase(player["role"], self.Lang("wolf")):
                _player = GamePlayerWolf(player, self)
            elif EqualIgnoreCase(player["role"], self.Lang("prophet")):
                _player = GamePlayerProphet(player, self)
            elif EqualIgnoreCase(player["role"], self.Lang("villager")):
                _player = GamePlayer(player, self)
            else:
                _player = None
            self.player_agents.append(_player)
            #print(self.player_agents[0].agent["summary_prompt"])
        pass
    
    ## clear Players Memory  
    def _clearPlayersMemory(self):
        for player in self.player_agents:
            player.ClearMemory()
        pass
    
    def Lang(self, key_path: str):
        keys = key_path.split(".")
        value = mappings
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    break
            else:
                raise TypeError(f"Cannot access key '{key}' from non-dictionary object")
        return value.get(self.lang)

    
    def DayVote(self, i) -> bool:
        # caculate the votes
        vote_names = []
        for vote in self.game_player_vote_log:
            if vote["time"] == self.current_time and vote["response"]["action"] == "PlayerVote":
                if vote["response"]["target"] != "" :
                    vote_names.append(vote["response"]["target"])
                    
        if len(vote_names) == 0:
            return False
        
        self.palyervotes = FindMostFrequent(vote_names)
        if len(self.palyervotes) != 1:
            for player in self.player_agents:
                # if player.agent["role"] == "狼人":
                #qKey = "player_vote_again" if len(self.palyervotes) > 1 else "player_vote_again_2"
                #question = self.game_config_dict["system"][qKey].format(",".join(self.palyervotes))
                question = self.Lang("system.player_vote_again").format(",".join(self.palyervotes))
                Info("[DAY_VOTE_AGAIN]" + question)
                self.game_system_log.append(question)
                self.game_player_vote_log.append(question)
                player.AddMemory(question)
            return False

        Info("\t player_vote_names: {0}".format(vote_names))
        vote_names_counter = Counter(vote_names)
        Debug("\t player_vote_names most_common: {0}\n".format(vote_names_counter.most_common(1)))
        elem, count = vote_names_counter.most_common(1)[0]
        Info("\t [player_votes]: {0}, [player_vote_name]: {1}".format(self.palyervotes, vote_names_counter))
        
        # kill the player and log it
        for player in self.roles_dict["players"]:
            if player["name"].strip() == elem.strip():
                Info("\t Day Vote player name: {0}".format(player["name"]))
                player["status"] = 0 # death !!!!
                player_log = self.Lang("MasterVote").format(self.current_time, player["name"])
                pub_log = ReadableActionLog("[DAY_VOTE]", self.current_time, elem, player_log)
                self.game_public_log.append(pub_log)
                vote_log = SystemLog("[DAY_VOTE]", self.current_time, player, player_log)
                self.game_system_log.append(vote_log)
                return True
                    
        return False
    
    def NightVote(self, i) -> bool:
        # caculate the votes
        vote_names = []
        # print(self.game_wolf_vote_log)
        # wolf vote caculate
        for vote in self.game_wolf_vote_log:
            if vote["time"] == self.current_time and vote["response"]["action"].lower().startswith('wolfvote'):
                if vote["response"]["target"] != "" :
                    vote_names.append(vote["response"]["target"])

        if len(vote_names) == 0:
            return False

        self.wolfvotes = FindMostFrequent(vote_names)
        # not on agreement, need to share memory
        if len(self.wolfvotes) != 1:
            for player in self.player_agents:
                if player.IsWolf():
                    #qKey = "wolf_vote_again" if len(self.wolfvotes) > 1 else "wolf_vote_again_2"
                    #question = self.game_config_dict["system"][qKey].format(",".join(self.wolfvotes))
                    
                    question = self.Lang("system.wolf_vote_again").format(",".join(self.wolfvotes))
                    Info("[NIGHT_VOTE_AGAIN]" + question)
                    self.game_system_log.append(question)
                    self.game_wolf_vote_log.append(question)
                    player.AddMemory(question)
            return False
        
        Debug("\t wolf_vote_names: {0}".format(vote_names))
        vote_names_counter = Counter(vote_names)
        Debug("\t wolf_vote_names most_common: {0}\n".format(vote_names_counter.most_common(1)))
        wolf_target, count = vote_names_counter.most_common(1)[0]
 
        Info("\t [wolfvotes]: {0}, [vote_names_counter]: {1}, [wolf_target]: {2}".format(self.wolfvotes, vote_names_counter, wolf_target))
        # kill the player and log it
        for player in self.roles_dict["players"]:
            if player["name"].strip() == wolf_target.strip():
                Debug("\t Night Vote player name: {0}".format(player["name"]))
                player["status"] = 0 # death !!!!
                player_log = self.Lang("MasterVote").format(self.current_time, player["name"])
                pub_log = ReadableActionLog("[NIGHT_VOTE]", self.current_time, player["name"] , player_log)
                self.game_public_log.append(pub_log)
                sys_log = SystemLog("[NIGHT_VOTE]", self.current_time, player, player_log)
                self.game_system_log.append(sys_log)
                return True
            
        return False
    
    def NightWitch(self, i):
        poision_names = []
        antidote_names = []
        # potion vote caculate
        for vote in self.game_witch_potion_log:
            # Witch Antidote
            if vote["time"] == self.current_time and vote["response"]["action"] == "WitchAntidote":
                if vote["response"]["target"] != "" :
                    antidote_names.append(vote["response"]["target"])
            # Witch Poision
            if vote["time"] == self.current_time and vote["response"]["action"] == "WitchPoision":
                if vote["response"]["target"] != "" :
                    poision_names.append(vote["response"]["target"])
            pass
        
        poision_target = "" if len(poision_names) == 0 else poision_names[0]
        antidote_target = "" if len(antidote_names) == 0 else antidote_names[0]
        Info("\t [poision_target]: {0}".format(poision_target))
        Info("\t [antidote_target]: {0}".format(antidote_target))
        for player in self.roles_dict["players"]:
            if player["name"].strip() == poision_target.strip():
                Info("\t NightWitch Poision player name: {0}".format(player["name"]))
                player["status"] = 0 # death !!!!
                player_log = self.Lang("WitchPoision").format(self.current_time, player["name"])
                pub_log = ReadableActionLog("[NIGHT_WITCH]", self.current_time, player["name"] , player_log)
                self.game_public_log.append(pub_log)
                sys_log = SystemLog("[NIGHT_WITCH]", self.current_time, player, player_log)
                self.game_system_log.append(sys_log)
                pass
                
            elif player["name"].strip() == antidote_target.strip():
                Info("\t NightWitch Antidote player name: {0}".format(player["name"]))
                player["status"] = 1 # alive !!!!
                player_log = self.Lang("WitchAntidote").format(self.current_time, player["name"])
                pub_log = ReadableActionLog("[NIGHT_WITCH]", self.current_time, player["name"] , player_log)
                self.game_public_log.append(pub_log)
                sys_log = SystemLog("[NIGHT_WITCH]", self.current_time, player, player_log)
                self.game_system_log.append(sys_log)
                pass
        pass
    
    def EndRoundCheck(self):
        self.winner = self._checkWinner()

        # message = self.game_config_dict["system"]["win_none"].format(GetAllPlayersName(self.roles_dict, self.lang))
        # if self.winner == 1:
        #     message = self.game_config_dict["system"]["win_villager"].format(GetAllPlayersName(self.roles_dict, self.lang))
        # if self.winner == 2:
        #     message = self.game_config_dict["system"]["win_wolf"].format(GetAllPlayersName(self.roles_dict, self.lang))
            
        message = self.Lang("system.win_none").format(GetAllPlayersName(self.roles_dict, self.lang))
        if self.winner == 1:
            message = self.Lang("system.win_villager").format(GetAllPlayersName(self.roles_dict, self.lang))
        if self.winner == 2:
            message = self.Lang("system.win_wolf").format(GetAllPlayersName(self.roles_dict, self.lang))
        
        if self.winner != 0 or not self.run:
            self.game_system_log.append(message)
            self.stage = GameStage.Assistant.value
            # assistant agent
            # summerize the game
            _template_assistant_role = self.player_agents[0].agent["summary_prompt"].replace("{num}", "1000")
            self.assistant = GameAssistant(_template_assistant_role, self, 1)
            memories = []
            # system message
            for log in self.game_system_log[-1000:]:
                memories.append(json.dumps(log, ensure_ascii=False))
            if len(memories) > 0:
                answer = self.assistant.DoAnswer(".".join(memories))
                
                output_message = {}
                output_message["player_id"] = 1000
                output_message["player_name"] = "game assistant"
                output_message["message"] = answer[len(answer)-1]
                output_message["is_day"] = self.isDay
                output_message["round"] = self.round
                output_message["current_time"] = self.current_time
                output_message["type"] = 0
                output_message["stage"] = self.stage
                self.game_output_queue.put(output_message)
            pass

        return message
    
    def GetMessages(self):
        messages = []
        while not self.game_output_queue.empty():
            messages.append(self.game_output_queue.get())
        output = {}
        output['messages'] = messages
        output['end'] = not self.inGame
        output['players'] = GetPlayerInfo(self.roles_dict, self.lang)
        return output
    
    def FakeEnding(self):
        self.stage = GameStage.Assistant.value
        output_message = {}
        output_message["player_id"] = 1000
        output_message["player_name"] = "game assistant"
        output_message["message"] = {}
        output_message["message"]["role"] = "assistant"
        output_message["message"]["content"] = "这是一段非常长的对话,"*20
        
        output_message["is_day"] = self.isDay
        output_message["round"] = self.round
        output_message["current_time"] = self.current_time
        output_message["type"] = 0
        output_message["stage"] = self.stage
        
        output = {}
        output['messages'] = [output_message]
        output['end'] = not self.inGame
        output['players'] = GetPlayerInfo(self.roles_dict, self.lang)
        return output

    def PreAction(self, i):
        if self.winner != 0:
            self.run = False
            return 
        Info("\t===== {0} PreAction ======".format(self._current_time(i)))
        
        if self.isDay:
            self.stage = GameStage.DeathWords.value
            for player in self.player_agents:
                if self.exit_flag:
                    self.run = False
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    #question_template = self.game_config_dict["player"]["action_plan_death"]
                    question_template = self.Lang("player.action_plan_death")
                    player.DoPlanning(question_template, i)
                    player.Die() ### never talk
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    pass
                pass
            pass
        else:
            sorted_players = SortedPlayersInNight(self.player_agents, self.lang)
            for player in sorted_players:
                if self.exit_flag:
                    self.run = False
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    pass
                pass
            pass
        pass
    
    def DoAction(self, i):
        if self.winner != 0:
            self.run = False
            return
        Info("\t===== {0} DoAction ======".format(self._current_time(i)))
        
        if self.isDay:
            self.stage = GameStage.DayDebate.value
            for player in self.player_agents:
                if self.exit_flag:
                    self.run = False
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    #question_template = self.game_config_dict["player"]["action_plan_day"]
                    question_template = self.Lang("player.action_plan_day")
                    player.DoPlanning(question_template, i)
                    pass
                pass
            pass
        else:
            # clean previous vote and potion log
            self.game_wolf_vote_log = []
            self.game_witch_potion_log = []
            
            self.stage = GameStage.NightAction.value
            sorted_players = SortedPlayersInNight(self.player_agents, self.lang)
            for player in sorted_players:
                if self.exit_flag:
                    self.run = False
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    if not player.IsVillager() and not player.IsWitch():
                        #question_template = self.game_config_dict["player"]["action_plan_night"]
                        question_template = self.Lang("player.action_plan_night")
                        player.DoPlanning(question_template, i)
                    pass
                pass
            pass
        pass

    def PostAction(self, i):
        if self.winner != 0:
            self.run = False
            return
        Info("\t===== {0} PostAction ======".format(self._current_time(i)))
        
        if self.isDay:
            self.stage = GameStage.DayVote.value
            # calculate votes
            while not self.DayVote(i):
                if self.exit_flag:
                    self.run = False
                    return
                # clean previous vote
                self.game_player_vote_log = []
                # reset votes
                self.palyervotes = []
                # start voting
                for player in self.player_agents:
                    # 如果玩家是死亡状态
                    if player.GetStatus() == -1:
                        pass
                    # 如果玩家是遗言状态
                    if player.GetStatus() == 0:
                        pass
                    # 如果玩家是存活状态
                    if player.GetStatus() == 1: 
                        #question_template = self.game_config_dict["player"]["action_plan_day_vote"]
                        question_template = self.Lang("player.action_plan_day_vote")
                        player.DoPlanning(question_template, i)
                        pass
                    pass
                pass
                
                if self.DayVote(i):
                    break
                #message = self.game_config_dict["system"]["player_vote_failed"].format(self.current_time, self.palyervotes)
                
                message = self.Lang("system.player_vote_failed").format(self.current_time, self.palyervotes)
                Info("\t====== "+ message)
                self.game_public_log.append(message)
                pass

            # leave death words
            for player in self.player_agents:
                if self.exit_flag:
                    self.run = False
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    #question_template = self.game_config_dict["player"]["action_plan_death"]
                    question_template = self.Lang("player.action_plan_death")
                    player.DoPlanning(question_template, i)
                    player.Die() ### never talk
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    pass
                pass

        else: # night post action
            self.stage = GameStage.NightAction.value
            while not self.NightVote(i):
                if self.exit_flag:
                    self.run = False
                    return
                #message = self.game_config_dict["system"]["wolf_vote_failed"].format(self.current_time)
                message = self.Lang("system.wolf_vote_failed").format(self.current_time)
                Info("\t====== "+ message)
                # self.game_wolf_vote_log.append(message)
                # reset votes
                self.wolfvotes = []
                # re poll
                self.DoAction(i)

                pass
            
            # witch action
            witch = GetPlayer(self.player_agents, self.Lang("witch"))
            if witch != None and witch.GetStatus() >= 0: 
                #question_template = self.game_config_dict["player"]["action_plan_night"]
                question_template = self.Lang("player.action_plan_night")
                witch.DoPlanning(question_template, i)
                
                self.NightWitch(i)
            pass
        
        message = self.EndRoundCheck()
        Info(message)
        pass
    
    def ResetGame(self, lang="cn"):
        self.lang = lang
        LANG = self.lang
         # prepare the envs
        self._resetGlobal()
        self._reviveRoles()
        self._setupPlayers()
        self._clearPlayersMemory()
        self.start_time = time.time()
        Info("\t===== {0} ResetGame =====".format(GetAllPlayersName(self.roles_dict, self.lang)))
        pass
    
    def EndGame(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        Info("===== {0} EndGame =====".format(GetAllPlayersName(self.roles_dict, self.lang)))
        Info("\t===== input_tokens: {0} output_tokens {1} ======".format(self.input_tokens, self.output_tokens))
        Info("\t===== elapsed_time: {0} ======".format(self.elapsed_time))
        pass
    
    def RunGame(self): 
        Info("\t===== {0} RunGame =====".format(GetAllPlayersName(self.roles_dict, self.lang)))
        i = 0
        while self.run and True:
            self.inGame = True
            Info("\t===== input_tokens: {0} output_tokens {1} ======".format(self.input_tokens, self.output_tokens))
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
            Info("\t===== elapsed_time: {0} ======".format(self.elapsed_time))
            # escape condition
            if i >= self.game_config_dict["max_round"]:
                Info("\t===== GAME OVER  =====")
                break
            # round increment   
            i = i+1
            self.i = i
            
            # day round
            if i > 1:
                self.isDay = True
                self.PreAction(i)
                self.DoAction(i)
                self.PostAction(i)
                if self.winner != 0:
                    Info("\t===== GAME OVER  =====")
                    break
                    
            # night round
            self.isDay = False
            self.PreAction(i)
            self.DoAction(i)
            self.PostAction(i)

            if self.winner != 0:
                Info("\t===== GAME OVER  =====")
                break
        self.inGame = False