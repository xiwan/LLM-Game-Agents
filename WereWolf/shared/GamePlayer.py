from . import *
from .PeTemplates import *
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayer:
    
    global game_config_dict, roles_dict
    
    def __init__(self, player, GM):
        self.GM = GM
        self.player_memory = ""
        self.agent = player
        template_role = self.agent["prompt"]
        _template_role = template_role
        #_template_role = template_role.replace("{nickname}", player["name"])
        #_template_role = _template_role.replace("{role}", player["role"])
        #_template_role = _template_role.replace("{character}", player["character"])
        #print(_template_role)
        logger.info("{0} is {1}".format(player["name"], player["role"]))
        
        self.template_role = LangchainMiniPromptTemplate(_template_role)
        self.inventory = []
        # player agent
        role_memory = LangchainMiniMemory(k=10)
        player["conversation"] = LangchainMini(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0", 
            stream=True, 
            memory=role_memory, 
            system=template_role)
        
        # assistant agent
        _template_assistant_role = template_assistant_role.replace("{num}", "144")
        self.assistant = GameAssistant(_template_assistant_role, GM)
        
        pass
  
    def RefreshInventory(self):
        if self.IsWitch():
            self.inventory = [1, 1] # 0 poision 1 antidote
    
    def _getItem(self, idx):
        if self.IsWitch():
            return self.inventory[idx]
        return -1
            
    def _useItem(self, idx): 
        if self.IsWitch(): # 0 poision 1 antidote
            self.inventory[idx] = max(0, min(self.inventory[idx], self.inventory[idx]-1))
        
    def _stateInfoBuilder(self):
        boardInfo = "目前场上玩家信息:{0}.".format(GetAllPlayersName())
        if self.IsWitch():
            boardInfo += "药水道具状态:毒药{0},解药{1}".format(self._getItem(0), self._getItem(1))
        return boardInfo
    
    def _playerInfoBuilder(self):
        roleInfo = self.agent["role"]
        extraInfo = ""
        if self.IsWolf():
            extraInfo += "本阵营玩家为:{0}.".format(GetAllWolvesName())
        playerInfo = game_config_dict["player"]["action_prefix"].format(self.agent["name"], self.agent["role"], self.agent["character"], extraInfo)
        return playerInfo 
    
    def _invoke(self, question):
        logger.info("\tQUESTION: " + question)
        _question = question
        #_question = self.template_role.format(input=question)
        #print(_question)
        answer = self.agent["conversation"].invoke(_question)
        return answer
    
    def _invokeAssistant(self, question):
        _question = self._stateInfoBuilder() + question
        logger.debug("\tASSISTANT QUESTION : " + _question)
        #print(_question)
        return self.assistant.DoAnswer(question)
    
    def Die(self):
        self.agent["status"] = -1
    
    def GetStatus(self):
        return self.agent["status"]
    
    def GetName(self):
        return self.agent["name"]

    def GetRole(self):
        return self.agent["role"]
    
    def IsWolf(self):
        return self.GetRole() == "狼人"
    
    def IsVillager(self):
        return self.GetRole() == "村民"
    
    def IsProphet(self):
        return self.GetRole() == "预言家"
    
    def IsWitch(self):
        return self.GetRole() == "女巫"
    
    def MessageRoleType(self):
        if self.IsVillager():
            return 1
        if self.IsProphet():
            return 2
        if self.IsWolf():
            return 3
        if self.IsWitch():
            return 4
        return 5 # assistant

    # answering question
    def DoAnswer(self, question):
        Info("\t\t******** DoAnswer {0} {1} ********".format(self.GM.current_time,self.agent["name"]))
        answer = self._invoke(question)
        return answer
    
    def DoPlanning(self, question_template, idx):
        if self.GM.exit_flag:
            return
        self.DoMemory()
        self.DoReflect()
        question = question_template.format(self._stateInfoBuilder(), self._playerInfoBuilder(), idx)
        answer = self.DoAnswer(question)
        self.DoAction(answer)
        time.sleep(5)
        pass
        
    def DoAction(self, answer):
        Info("\t\t******** DoAction {0} {1} ********".format(self.GM.current_time, self.agent["name"]))
        if answer == "":
            return
 
        try:
            output_message = {}
            output_message["player_id"] = self.agent["id"]
            output_message["player_name"] = self.agent["name"]
            output_message["message"] = answer[len(answer)-1]
            output_message["is_day"] = self.GM.isDay
            output_message["round"] = self.GM.round
            output_message["current_time"] = self.GM.current_time
            output_message["type"] = self.MessageRoleType()
            
            self.GM.game_output_queue.put(output_message)
        except queue.Full:
            print('game_output_queue.Full')
            
        response = ParseJson(answer[len(answer)-1]["content"])
        memories = []
        for res in response:
            res_obj = json.loads(res)
            log = ""
            if not "action" in res_obj:
                continue
            if res_obj["action"] == "ProphetCheck":
                if not self.GM.isDay:
                    memory = GetPlayerRole(res_obj["target"])
                    # print(memory)
                    log = ReadableActionLog("prophet_check_log", self.GM.current_time, self.agent, res_obj)
                    # self.GM.game_prophet_check_log.append(log)
                    self.GM.game_prophet_check_log.append(memory)
                    Info(log + " 结果 " +memory)
                    #log = ReadableActionLog("prophet_check_log", self.GM.current_time, self.agent, res_obj)
                    # self.GM.game_pulbic_log.append(log)
                pass
            
            if res_obj["action"] == "WolfVote":
                if not self.GM.isDay:
                    log = ActionLog("wolf_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_wolf_vote_log.append(log)
                    log = ReadableActionLog("wolf_vote_log", self.GM.current_time, self.agent, res_obj)
                pass
                
            if res_obj["action"] == "PlayerVote":
                if self.GM.isDay:
                    log = ActionLog("player_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_vote_log.append(log)
                    log = ReadableActionLog("player_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                    #self.GM.game_memory_queue.put(log)
                pass

            if res_obj["action"] == "PlayerDoubt":
                if self.GM.isDay:
                    log = ReadableActionLog("player_doubt_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                    #self.GM.game_memory_queue.put(log)
                pass

            if res_obj["action"] == "Debate":
                if self.GM.isDay:
                    log = ActionLog("player_debate_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_action_log.append(log)
                    log = ReadableActionLog("player_debate_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                    #self.GM.game_memory_queue.put(log)
                pass
           
            if res_obj["action"] == "DeathWords":
                if self.GM.isDay:
                    log = ActionLog("player_deathwords_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_action_log.append(log)
                    log = ReadableActionLog("player_deathwords_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                    # make it system message
                    # self.GM.game_memory_queue.put(log)
                pass
            
            memories.append(log)

        self.GM.game_system_log.append(SystemLog("[ROUND ACTION]", self.GM.current_time, self.agent, response))
        pass
        
    def DoMemory(self, memorysize=20):
        Info("\t\t******** DoMemory {0} {1} ********".format(self.GM.current_time, self.agent["name"]))
        
        memories = []
        # only for worlf
        if self.IsWolf():
            for log in self.GM.game_wolf_vote_log[-1*memorysize:]:
                memories.append(json.dumps(log, ensure_ascii=False))
                pass
        
        # only for prophet
        if self.IsProphet():
            for log in self.GM.game_prophet_check_log[-1*memorysize:]:
                memories.append(json.dumps(log, ensure_ascii=False))
                pass
            
        # only for witch
        if self.IsWitch():
            pass
            
        for log in self.GM.game_pulbic_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
            pass
        
        if len(memories) > 0:
            Info(memories)
            summary = self._invokeAssistant(".".join(memories))
            _summary = summary[len(summary)-1]["content"]
            self.AddMemory(_summary)
        time.sleep(5)
        pass
    
    def AddMemory(self, memory):
        self.player_memory = memory
        self.agent["conversation"].addMemory(memory)
        # output = game_config_dict["player"]["action_confirm"]
        # self.agent["conversation"].memory.save_context({"input": memory}, {"ouput": output})
    
    def DoReflect(self, memorysize=20):
        if self.GM.quick:
            return
    