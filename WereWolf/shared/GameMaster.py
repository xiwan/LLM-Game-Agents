from . import *
from .PeTemplates import *
from .GameAssistant import GameAssistant
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GameMaster:
    
    global game_config_dict, roles_dict
    
    def __init__(self, num, queueSize=10, quick=False) -> None:
        self.quick = quick
        self.queueSize = queueSize
        self._resetGlobal()
        
        game_config_dict["max_round"] = num
        pass
        
        
    def _resetGlobal(self):
        self.run = True
        self.exit_flag = False
        self.round = 0
        self.isDay = False
        self.current_time = ""
        self.game_memory_queue = queue.Queue(maxsize=self.queueSize)
        self.game_output_queue = queue.Queue(maxsize=self.queueSize)
        self.game_pulbic_log = []
        self.game_wolf_vote_log = []
        self.game_player_vote_log = []
        self.game_prophet_check_log = []
        self.game_player_action_log = []
        self.game_player_death_log = []
        self.game_system_log = []

        self.player_agents = []
        self.winner = 0  # 0: 继续 1: 村民 2:狼人
        
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
            self.current_time = "DAY {0}".format(self.round)
        else:
            self.current_time = "NIGHT {0}".format(self.round)
        return self.current_time
    
    def _reviveRoles(self):
        for player in roles_dict["players"]:
            player["status"] = 1
            
    def _checkWinner(self) -> str:
        """CheckWinner"""
        grouped_dict = GroupAllPlayers()
        message = "\t时间{0},场上存活状态 狼人:{1} 村民:{2}".format(self.current_time, str(len(grouped_dict["狼人"])), str(len(grouped_dict["村民"])))

        if len(grouped_dict["狼人"]) == 0 and len(grouped_dict["村民"]) > 0:
            return 1
        if len(grouped_dict["狼人"]) > 0 and len(grouped_dict["村民"]) <= len(grouped_dict["狼人"]):
            return 2 
        return 0
            
    ## setup Players
    def _setupPlayers(self):
        # cache the player agents
        for player in roles_dict["players"]:
            _player = GamePlayer(player, self)
            _player.RefreshInventory()
            self.player_agents.append(_player)
        pass
    
    ## clear Players Memory  
    def _clearPlayersMemory(self):
        for player in roles_dict["players"]:
            player["conversation"].clear()
        pass
    
    def PlayerVote(self, i) -> bool:
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
                question =""
                if len(self.palyervotes) > 1:
                    question = game_config_dict["system"]["player_vote_again"].format(",".join(self.palyervotes))
                if len(self.palyervotes) == 0:
                    question = game_config_dict["system"]["player_vote_again_2"].format(",".join(self.palyervotes))
                Info(question)
                self.game_system_log.append(question)
                player.AddMemory(question)
            return False
                
        Debug("\t player_vote_names: {0}".format(vote_names))
        vote_names_counter = Counter(vote_names)
        Debug("\t player_vote_names most_common: {0}\n".format(vote_names_counter.most_common(1)))
        elem, count = vote_names_counter.most_common(1)[0]
        Info("\t [player_votes]: {0}, [player_vote_name]: {1}".format(self.palyervotes, vote_names_counter))
        
        # kill the player and log it
        if elem != "":
            for player in roles_dict["players"]:
                Debug("\t player name: {0}".format(player["name"]))
                if player["name"] == elem:
                    player["status"] = 0 # death !!!!
                    player_log = "玩家{0}于{1}被玩家投票而出局".format(elem, self.current_time)
                    pub_log = ReadableActionLog("[PLAYER VOTE]", self.current_time, player, player_log)
                    self.game_pulbic_log.append(pub_log)
                    # for god
                    self.game_memory_queue.put(pub_log)
                    vote_log = SystemLog("[PLAYER VOTE]", self.current_time, player, player_log)
                    self.game_system_log.append(vote_log)
                    return True
                    
        return False
    
    def WolfVote(self, i) -> bool:
        # caculate the votes
        vote_names = []
        for vote in self.game_wolf_vote_log:
            if vote["time"] == self.current_time and vote["response"]["action"] == "WolfVote":
                if vote["response"]["target"] != "" :
                    vote_names.append(vote["response"]["target"])
                    
        if len(vote_names) == 0:
            return False
        
        self.wolfvotes = FindMostFrequent(vote_names)
        # not on agreement, need to share memory
        if len(self.wolfvotes) != 1:
            for player in self.player_agents:
                if player.IsWolf():
                    question =""
                    if len(self.wolfvotes) > 1:
                        question = game_config_dict["system"]["wolf_vote_again"].format(",".join(self.wolfvotes))
                    if len(self.wolfvotes) == 0:
                        question = game_config_dict["system"]["wolf_vote_again_2"].format(",".join(self.wolfvotes))
                    Info(question)
                    self.game_system_log.append(question)
                    self.game_wolf_vote_log.append(question)
                    player.AddMemory(question)
            return False
        
        Debug("\t wolf_vote_names: {0}".format(vote_names))
        vote_names_counter = Counter(vote_names)
        Debug("\t wolf_vote_names most_common: {0}\n".format(vote_names_counter.most_common(1)))
        elem, count = vote_names_counter.most_common(1)[0]
        Info("\t [wolf_votes]: {0}, [player_vote_name]: {1}".format(self.wolfvotes, vote_names_counter))
        
        # kill the player and log it
        if elem != "":
            for player in roles_dict["players"]:
                Debug("\t player name: {0}".format(player["name"]))
                if player["name"] == elem:
                    player["status"] = 0 # death !!!!
                    
                    player_log = "玩家{0}于{1}被狼人投票而出局".format(elem, self.current_time)
                    pub_log = ReadableActionLog("[WOLF VOTE]", self.current_time, player, player_log)
                    self.game_pulbic_log.append(pub_log)
                    # for god
                    self.game_memory_queue.put(pub_log)
                    sys_log = SystemLog("[WOLF VOTE]", self.current_time, player, player_log)
                    self.game_system_log.append(sys_log)
                    return True
        return False
    
    def EndRoundCheck(self):
        self.winner = self._checkWinner()

        message = game_config_dict["system"]["win_none"].format(GetAllPlayersName())
        if self.winner == 1:
            message = game_config_dict["system"]["win_villager"].format(GetAllPlayersName())
        if self.winner == 2:
            message = game_config_dict["system"]["win_wolf"].format(GetAllPlayersName())
   
        if self.winner != 0:
            self.game_system_log.append(message)
            
            # assistant agent
            # summerize the game
            _template_assistant_role = template_assistant_role.replace("{num}", "1000")
            self.assistant = GameAssistant(_template_assistant_role, self)
            memories = []
            # system message
            for log in self.game_system_log[-1000:]:
                memories.append(json.dumps(log, ensure_ascii=False))
            if len(memories) > 0:
                output = self.assistant.DoAnswer(".".join(memories))
            pass

        return message
    
    def GetMessages(self):
        messages = []
        while not self.game_output_queue.empty():
            messages.append(self.game_output_queue.get())
        return messages

    def PreAction(self, i):
        if self.winner != 0:
            self.run = False
            return 
        Info("\t===== {0} PreAction ======".format(self._current_time(i)))
        
        if self.isDay:
            for player in self.player_agents:
                if self.exit_flag:
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    question_template = game_config_dict["player"]["action_plan_death"]
                    player.DoPlanning(question_template, i)
                    player.Die() ### never talk
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    pass
                pass
            pass
        else:
            sorted_players = SortedPlayersInNight(self.player_agents)
            for player in sorted_players:
                if self.exit_flag:
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
            for player in self.player_agents:
                if self.exit_flag:
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    question_template = game_config_dict["player"]["action_plan_day"]
                    player.DoPlanning(question_template, i)
                    pass
                pass
            pass
        else:
            # clean previous vote
            self.game_wolf_vote_log = []
            sorted_players = SortedPlayersInNight(self.player_agents)
            for player in sorted_players:
                if self.exit_flag:
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    if not player.IsVillager():
                        question_template = game_config_dict["player"]["action_plan_night"]
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
            # calculate votes
            while not self.PlayerVote(i):
                if self.exit_flag:
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
                        question_template = game_config_dict["player"]["action_plan_day_vote"]
                        player.DoPlanning(question_template, i)
                        pass
                    pass
                pass
                
                if self.PlayerVote(i):
                    break
                message = "时间{0}, 玩家没有统一选择.玩家重新在{1}中选择嫌疑人投票!".format(self.current_time, self.palyervotes)
                Info("\t====== "+ message)
                self.game_pulbic_log.append(message)
                pass

            # leave death words
            for player in self.player_agents:
                if self.exit_flag:
                    return
                # 如果玩家是死亡状态
                if player.GetStatus() == -1:
                    pass
                # 如果玩家是遗言状态
                if player.GetStatus() == 0:
                    question_template = game_config_dict["player"]["action_plan_death"]
                    player.DoPlanning(question_template, i)
                    player.Die() ### never talk
                    pass
                # 如果玩家是存活状态
                if player.GetStatus() == 1: 
                    pass
                pass

        else: # night post action
            while not self.WolfVote(i):
                if self.exit_flag:
                    return
                message = "时间{0}, 狼人没有统一选择, 夜晚必须要投出一名玩家.".format(self.current_time)
                Info("\t====== "+ message)
                # self.game_wolf_vote_log.append(message)
                # reset votes
                self.wolfvotes = []
                # re poll
                self.DoAction(i)

                pass
        
        message = self.EndRoundCheck()
        Info(message)
        pass
    
    def ResetGame(self):
        LoadPlayerPrompts()
        self.start_time = time.time()
        Info("\t===== {0} ResetGame =====".format(GetAllPlayersName()))
         # prepare the envs
        self._resetGlobal()
        self._reviveRoles()
        self._setupPlayers()
        self._clearPlayersMemory()

        pass
    
    def EndGame(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        Info("===== {0} EndGame =====".format(GetAllPlayersName()))
        Info("\t===== input_tokens: {0} output_tokens {1} ======".format(self.input_tokens, self.output_tokens))
        Info("\t===== elapsed_time: {0} ======".format(self.elapsed_time))
        pass
    
    def RunGame(self): 
        Info("\t===== {0} RunGame =====".format(GetAllPlayersName()))
        i = 0
        while self.run and True:
            Info("\t===== input_tokens: {0} output_tokens {1} ======".format(self.input_tokens, self.output_tokens))
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
            Info("\t===== elapsed_time: {0} ======".format(self.elapsed_time))
            # escape condition
            if i >= game_config_dict["max_round"]:
                Info("游戏结束.")
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
                    Info("游戏结束.")
                    break
                    
            # night round
            self.isDay = False
            self.PreAction(i)
            self.DoAction(i)
            self.PostAction(i)

            if self.winner != 0:
                Info("游戏结束.")
                break