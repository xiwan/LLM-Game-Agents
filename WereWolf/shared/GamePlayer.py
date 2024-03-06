from . import *
from .PeTemplates import *
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayer:
    
    global game_config_dict, roles_dict
    
    def __init__(self, template_role, player, GM):
        self.GM = GM
        self.agent = player
        
        _template_role = template_role.replace("{nickname}", player["name"])
        _template_role = _template_role.replace("{role}", player["role"])
        _template_role = _template_role.replace("{character}", player["character"])
        
        logger.info("{0} is {1}".format(player["name"], player["role"]))
        
        self.template_role = LangchainMiniPromptTemplate(_template_role)
        
        # player agent
        role_memory = LangchainMiniMemory(k=10)
        player["conversation"] = LangchainMini(model_id="anthropic.claude-3-sonnet-20240229-v1:0", stream=True, memory=role_memory)
        
        # assistant agent
        _template_assistant_role = template_assistant_role.replace("{num}", "100")
        self.assistant = GameAssistant(_template_assistant_role, GM)
        
        pass
    
    def _invoke(self, question):
        logger.info("\tQUESTION: " + question)
        _question = self.template_role.format(input=question)
        answer = self.agent["conversation"].invoke(_question)
        return answer
    
    def _invokeAssistant(self, question):
        teamexplain = "(初始配置为2狼人+1预言家+5村民, 每轮发言顺序为P1,P2,P3,P4,P5,P6,P7,P8)"
        boardInfo = "[目前场上信息:{0}{1}.] ".format(GetAllPlayersName(), teamexplain)
        question = boardInfo + question
        logger.debug("\tASSISTANT QUESTION : " + question)
        return self.assistant.DoAnswer(question)
    
    def _playerInfoBuilder(self):
        boardInfo = "目前场上玩家:{0}(逗号为分割符).".format(GetAllPlayersName())
        if self.IsWolf():
            playerInfo = "现在是{0},你支持的玩家是{1}(狼人,本阵营为:{2}).{3}".format(self.GM.current_time, self.agent["name"], GetAllWolvesName(), boardInfo)
        if self.IsVillager():
            playerInfo = "现在是{0},你支持的玩家是{1}(村民).{2}.{3}".format(self.GM.current_time, self.agent["name"], "", boardInfo)
        if self.IsProphet():
            playerInfo = "现在是{0},你支持的玩家是{1}(预言家).{2}.{3}".format(self.GM.current_time, self.agent["name"], "",  boardInfo)
        return playerInfo
    
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
    
    # answering question
    def DoAnswer(self, question):
        Info("\t\t===== DoAnswer {0} {1} ======".format(self.GM.current_time,self.agent["name"]))
        answer = self._invoke(question)
        return answer
    
    def DoPlanning(self, question_template, idx):
        self.DoMemory()
        self.DoReflect()
        question = question_template.format(self._playerInfoBuilder(), "", idx)
        answer = self.DoAnswer(question)
        self.DoAction(answer)
        pass
        
    def DoAction(self, answer):
        Info("\t\t===== DoAction {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        if answer == "":
            return
        
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
                    self.GM.game_prophet_check_log.append(log)
                    self.GM.game_prophet_check_log.append(memory)
                    Info(log + memory)
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

            if res_obj["action"] == "GetAllPlayersName":
                memory = game_config_dict["system"]["board"].format(GetAllPlayersName())
                
                log = ActionLog("player_check_log", self.GM.current_time, self.agent, res_obj)
                self.GM.game_player_action_log.append(log)
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
        
    def DoMemory(self, memorysize=100):
        Info("\t\t===== DoMemory {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        
        memories = []
        for log in self.GM.game_pulbic_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
            pass
        
        if self.IsWolf():
            for log in self.GM.game_wolf_vote_log[-1*memorysize:]:
                memories.append(json.dumps(log, ensure_ascii=False))
                pass
            
        if self.IsProphet():
            for log in self.GM.game_prophet_check_log[-1*memorysize:]:
                memories.append(json.dumps(log, ensure_ascii=False))
                pass
            
        if len(memories) > 0:
            summary = self._invokeAssistant(".".join(memories))
            self.AddMemory(summary)
        pass
    
    def AddMemory(self, memory):
        Debug(memory)
        # output = game_config_dict["player"]["action_confirm"]
        # self.agent["conversation"].memory.save_context({"input": memory}, {"ouput": output})
    
    def DoReflect(self, memorysize=20):
        if self.GM.quick:
            return
    