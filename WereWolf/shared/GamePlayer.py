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
        template_role = self.agent["prompt"]
        
        _template_role = template_role.replace("{formation}", GetPartySize())
        # _template_role = _template_role.replace("{nickname}", player["name"])
        # _template_role = _template_role.replace("{role}", player["role"])
        # _template_role = _template_role.replace("{character}", player["character"])
        
        # Info(_template_role)
        Info("{0} is {1}".format(player["name"], player["role"]))
        
        self.template_role = LangchainMiniPromptTemplate(_template_role)

        # player agent
        role_memory = LangchainMiniMemory(k=10)
        player["conversation"] = LangchainMini(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0", 
            stream=True, 
            memory=role_memory, 
            system=template_role)
        
        # assistant agent
        _template_assistant_summarize_role = template_assistant_summarize_role.replace("{num}", "144")
        self.assistant = GameAssistant(_template_assistant_summarize_role, GM)
        pass

    def _stateInfoBuilder(self):
        boardInfo = "目前玩家状态:{0}.".format(GetAllPlayersName())
        return boardInfo
    
    def _playerInfoBuilder(self):
        extraInfo = "阵营为:{0}.本阵营队友未知".format(GetPartySize())
        playerInfo = game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
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
    
    def DoPlanning(self, question_template, idx):
        if self.GM.exit_flag:
            return
        self.DoMemory()
        self.DoReflect()
        question = question_template.format(self._stateInfoBuilder(), self._playerInfoBuilder(), idx)
        answer = self.DoAnswer(question)
        response = self.DoValidate(question, answer)
        self.DoAction(response)
        time.sleep(3)
        pass

    # answering question
    def DoAnswer(self, question):
        self.InfoMessage("DoAnswer")
        answer = self._invoke(question)
        return answer

    def DoValidate(self, question, answer):
        self.InfoMessage("DoValidate")
        self.questionTry = self.questionTry - 1
        if answer == "" or self.questionTry == 0:
            return []

        # Info(answer)
        response = ParseJson(answer[len(answer)-1]["content"])
        # Info(response)
        validJsonFlag = True
        for res in response:
            if not IsValidJson(res):
                validJsonFlag = False
                break
          
        if response is None or not validJsonFlag:
            Info("\t\t BAD RESPONSE: {0} {1}".format(response, self.questionTry))
            answer = self.DoAnswer(question)
            return self.DoValidate(question, answer)
            
        Info("\t\t DoValidate: {0}".format(response))
        self.BuildOutputMessage(answer[len(answer)-1], self.MessageRoleType())
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
        self.agent["conversation"].addMemory(memory)
    
    def DoReflect(self, memorysize=20):
        if self.GM.quick:
            return
    
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
            
            self.GM.game_output_queue.put(output_message)
        except queue.Full:
            logger.exception('game_output_queue.Full')
        pass