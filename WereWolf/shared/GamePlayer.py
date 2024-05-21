from . import *
from .PeTemplates import *
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayer:
    global game_config_dict, roles_dict
    
    def __init__(self, player, GM):
        self.questionTry = 3
        self.GM = GM
        self.player_memory = ""
        self.agent = player
        self.reflectTimes = 0
        self.reflectScore = 0
        
        Info("name: {0} role: {1} gender: {2}".format(player["name"], player["role"], player["gender"]))

        # player agent
        action_role = self.agent["action_prompt"]
        _action_role = action_role.replace("{formation}", GetPartySize())
        # Info(_action_role)
        player["actor"] = GameAssistant(_action_role, GM, 10)

        # reflect agent
        reflect_role = self.agent["reflect_prompt"]
        _reflect_role = reflect_role.replace("{formation}", GetPartySize())
        player["reflector"] = GameAssistant(_reflect_role, GM, 5)
        
        # assistant agent
        summary_role = self.agent["summary_prompt"]
        _summary_role = summary_role.replace("{num}", "144")
        player["assistant"] = GameAssistant(_summary_role, GM)
        pass

    def _stateInfoBuilder(self):
        boardInfo = ""
        #if self.reflectScore > 0:
        #    boardInfo += "上轮决策评分:{0}.".format(self.reflectScore)
        boardInfo += "目前玩家状态:{0}.".format(GetAllPlayersName())
        return boardInfo
    
    def _playerInfoBuilder(self):
        extraInfo = "阵营为:{0}.本阵营队友未知".format(GetPartySize())
        playerInfo = game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo 
    
    def Die(self):
        self.agent["status"] = -1
    
    def GetStatus(self):
        return self.agent["status"]
    
    def GetName(self):
        return self.agent["name"]

    def GetRole(self):
        return self.agent["role"]
    
    def GetCharacter(self):
        return self.agent["character"]
    
    def IsWolf(self):
        return self.GetRole() == "狼人"
    
    def IsVillager(self):
        return self.GetRole() == "村民"
    
    def IsProphet(self):
        return self.GetRole() == "预言家"
    
    def IsWitch(self):
        return self.GetRole() == "女巫"
    
    def MessageRoleType(self):
        if self.IsVillager(): # villager
            return 1
        if self.IsProphet(): # prophet
            return 2
        if self.IsWolf(): # wolf
            return 3
        if self.IsWitch(): # witch
            return 4
        return 0 # assistant
    
    def InfoMessage(self, title):
        Info("\t\t******** {0} {1} {2} {3}********".format(title, self.GM.current_time, self.GetName(), self.GetRole()))
    
    def UsePlayerValidate(self, abilityName, target=None, item=None):
        pass
    
    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = None
        if not self.GM.isDay:
            return log
        
        if abilityName == "PlayerVote":
            log = ActionLog("player_vote_log", self.GM.current_time, self.agent, item)
            self.GM.game_player_vote_log.append(log)
            log = ReadableActionLog("player_vote_log", self.GM.current_time, self.agent["name"], item)
            self.GM.game_public_log.append(log)
            pass
        if abilityName == "PlayerDoubt":
            log = ReadableActionLog("player_doubt_log", self.GM.current_time, self.agent["name"], item)
            self.GM.game_public_log.append(log)
        if abilityName == "Debate":
            log = ActionLog("player_debate_log", self.GM.current_time, self.agent, item)
            self.GM.game_player_action_log.append(log)
            log = ReadableActionLog("player_debate_log", self.GM.current_time, self.agent["name"], item)
            self.GM.game_public_log.append(log)
            pass
        if abilityName == "DeathWords":
            log = ActionLog("player_deathwords_log", self.GM.current_time, self.agent, item)
            self.GM.game_player_action_log.append(log)
            log = ReadableActionLog("player_deathwords_log", self.GM.current_time, self.agent["name"], item)
            self.GM.game_public_log.append(log)
            pass
        return log
    
    def _invokeActor(self, question, reflect=False):
        logger.info("\tACTOR QUESTION: " + question)
        #print(_question)
        answer = self.agent["actor"].DoAnswer(question)
        return answer
    
    def _invokeReflector(self, question, reflect=False):
        logger.info("\tREFLECT QUESTION: " + question)
        _question = question
        #print(_question)
        answer = self.agent["reflector"].DoAnswer(_question)
        return answer
    
    def _invokeAssistant(self, question):
        _question = question
        logger.debug("\tASSISTANT QUESTION : " + _question)
        #print(_question)
        return self.agent["assistant"].DoAnswer(question)

    def DoPlanning(self, question_template, idx):
        self.idx = idx
        self.question_template = question_template
        if self.GM.exit_flag:
            return
        self.DoMemory(memories=[])
        question = self.question_template.format(self._stateInfoBuilder(), self._playerInfoBuilder(), self.idx)
        answer = self.DoAnswer(question)
        answer = self.DoValidate(question, answer)
        self.DoAction(answer)
        time.sleep(3)
        pass
    
    # answering question
    def DoAnswer(self, question):
        self.InfoMessage("DoAnswer")
        if self.reflectScore > 0:
            question = self.question_template.format(self._stateInfoBuilder(), self._playerInfoBuilder(), self.idx)
            question = "上轮决策评分:{0}.建议调整策略.".format(self.reflectScore) + question
        answer = self._invokeActor(question)
        answer = self.DoReflect(question, answer)
        return answer

    def DoReflect(self, question, answer):
        # Info(answer)
        if self.GM.quick:
            return answer
        self.InfoMessage("DoReflect")
        answer = [ConvertToJson(answer[len(answer)-1])]
        response = ParseJson(answer[len(answer)-1]["content"])

        relfect_question = "游戏进度:{1}.玩家信息:{2}. 时间:{0}.玩家决策:{3}.".format(
            self.GM.current_time, 
            self._stateInfoBuilder(), 
            self._playerInfoBuilder(), 
            json.dumps(response,  ensure_ascii=False))
        reflect = self._invokeReflector(relfect_question)
        
        reflect = [ConvertToJson(reflect[len(reflect)-1])]
        reflectResponse = ParseJson(reflect[len(reflect)-1]["content"])
        for res in reflectResponse:
            res_obj = json.loads(res)
            if not "score" in res_obj:
                res_obj["score"] = game_config_dict["reflect_treshhold"] - 1
            if res_obj["score"] < game_config_dict["reflect_treshhold"] and self.reflectTimes < 3:
                self.reflectTimes += 1
                self.reflectScore = res_obj["score"]
                return self.DoAnswer(question)
        
        Info("\t\t DoReflect: {0}".format(reflectResponse))
        self.BuildOutputMessage(reflect[len(reflect)-1], self.MessageRoleType()) 
        self.reflectScore = 0
        return answer
    
    def DoValidate(self, question, answer):
        self.InfoMessage("DoValidate")
        self.questionTry = self.questionTry - 1
        if answer == "" or len(answer) == 0 or self.questionTry == 0:
            return []

        #Info(answer)
        answer = [ConvertToJson(answer[len(answer)-1])]
        response = {}
        if 'content' in answer[len(answer)-1] and answer[len(answer)-1]['content']:
            response = ParseJson(answer[len(answer)-1]["content"])
        else:
            response = answer[len(answer)-1]
        # Info(response)
        validJsonFlag = True
        for res in response:
            if not IsValidJson(res):
                validJsonFlag = False
                break
          
        if response is None or not validJsonFlag:
            Info("\t\t BAD RESPONSE AND PASS: {0} {1}".format(response, self.questionTry))
            return {}
            
        Info("\t\t DoValidate: {0}".format(response))
        self.BuildOutputMessage(answer[len(answer)-1], 0)
        self.questionTry = 3
        return response
        
    def DoAction(self, response):
        self.InfoMessage("DoAction")
        memories = []
        for res in response:
            res_obj = json.loads(res)
            log = None
            if not "action" in res_obj:
                continue
                
            res_obj["action_time"] = self.GM.current_time
            if "target" in res_obj:
                log = self.UsePlayerAbility(res_obj["action"], res_obj["target"], res_obj)
            else:
                log = self.UsePlayerAbility(res_obj["action"], None, res_obj)
            
            if not log is None: 
                memories.append(log)

        self.GM.game_system_log.append(SystemLog("[ROUND ACTION]", self.GM.current_time, self.agent, response))           
        pass
        
    def DoMemory(self, memorysize=10, memories=[]):
        self.InfoMessage("DoMemory")
        for log in self.GM.game_public_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))

        if len(memories) > 0:
            # Info(memories)
            logs = ".".join(memories)
            # print("memories: " + logs)
            summary = self._invokeAssistant(logs)
            _summary = summary[len(summary)-1]["content"]
            self.AddMemory(_summary)
            
            self.BuildOutputMessage(summary[len(summary)-1], 0)
        time.sleep(3)
        return memories
    
    def AddMemory(self, memory):
        self.player_memory = memory
        self.agent["actor"].AddMemory(memory)
        
    def ClearMemory(self):
        self.InfoMessage("ClearMemory")
        self.player_memory = ""
        self.agent["actor"].Clear()
        self.agent["reflector"].Clear()
        self.agent["assistant"].Clear()

    def BuildOutputMessage(self, message, messageType=0):
        try:
            output_message = {}
            output_message["player_id"] = self.agent["id"]
            output_message["player_name"] = self.agent["name"]
            output_message["message"] = message
            output_message["is_day"] = self.GM.isDay
            output_message["round"] = self.GM.round
            output_message["current_time"] = self.GM.current_time
            output_message["type"] = messageType
            output_message["stage"] = self.GM.stage
            
            # Info("\t\t BuildOutputMessage: {0}".format(output_message))
            self.GM.game_output_queue.put(output_message)
        except queue.Full:
            logger.exception('game_output_queue.Full')
        pass