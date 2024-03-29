import json,time
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .GameAssistant import GameAssistant
from .PeTemplates import *

class GamePlayer:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, player, GM):
        self.GM = GM

        _template_role = template_role.replace("{nickname}", player["name"])
        _template_role = _template_role.replace("{role}", player["role"])
        _template_role = _template_role.replace("{character}", player["character"])

        Info("{0} is {1}".format(player["name"], player["role"]))

        _template_role_prompt = PromptTemplate.from_template(_template_role)
        #_template_role_prompt.format(nickname=player["name"], role=player["role"], character=player["character"])

        role_memory = ConversationBufferWindowMemory(k = 10, return_messages=True,
                                                     human_prefix="Human", ai_prefix="Assistant", 
                                                     memory_key="chat_history", input_key="input")
        
        # role_memory = ConversationSummaryBufferMemory(llm=self.GM.llm, max_token_limit=200, return_messages=True, 
        #                                               human_prefix="Human", ai_prefix="Assistant", 
        #                                               memory_key="chat_history", input_key="input")

        player["conversation"] = ConversationChain(
            prompt=_template_role_prompt,
            llm=self.GM.llm, 
            verbose=False, 
            memory=role_memory
        )
        Debug(player["conversation"])

        self.token_counter = self.GM.token_counter # AnthropicTokenCounter(claude_llm)
        self.agent = player
        
        _template_assistant_role = template_assistant_role.replace("{num}", "100")
        self.assistant = GameAssistant(_template_assistant_role, GM)

        self.assitant_api = GameAssistant(template_assistant_api_role, GM)
        pass
    
    def _invoke(self, question):
        Info("\tQUESTION: " + question)
        time.sleep(500 / 1000)
        answer = self.agent["conversation"].invoke(input = question, config={"callbacks": [self.token_counter]})
        self.GM.input_tokens = self.GM.input_tokens + self.token_counter.input_tokens
        self.GM.output_tokens = self.GM.output_tokens + self.token_counter.output_tokens
        return answer
    
    def _invokeAssistant(self, question):
        teamexplain = "(初始配置为2狼人+6村民, 每轮发言顺序为P1,P2,P3,P4,P5,P6,P7,P8)"
        boardInfo = "[目前场上信息:{0}{1}.] ".format(GetAllPlayersName(), teamexplain)
        question = boardInfo + question
        Debug("\tASSISTANT QUESTION : " + question)
        return self.assistant.DoAnswer(question)
    
    def _invokeAssistantApi(self, question):
        Debug("\tASSISTANT API QUESTION : " + question)
        return self.assitant_api.DoAnswer("{0}. 按照要求归类".format(question))
    
    def _playerInfoBuilder(self):
        boardInfo = "目前场上玩家:{0}(逗号为分割符).".format(GetAllPlayersName())
        if self.IsWolf():
            playerInfo = "现在是{2},你支持的玩家是{0}(狼人身份,本阵营为:{1}).{3}".format(self.agent["name"], GetAllWolvesName(), self.GM.current_time, boardInfo)
        if self.IsVillager():
            playerInfo = "现在是{2},你支持的玩家是{0}(村民身份).{1}.{3}".format(self.agent["name"], "", self.GM.current_time, boardInfo)
        if self.IsProphet():
            playerInfo = "现在是{2},你支持的玩家是{0}(预言家身份).{1}.{3}".format(self.agent["name"], "", self.GM.current_time, boardInfo)
        return playerInfo
    
    def IsWolf(self):
        return self.GetRole() == "狼人"
    
    def IsVillager(self):
        return self.GetRole() == "村民"
    
    def IsProphet(self):
        return self.GetRole() == "预言家"
    
    def Die(self):
        self.agent["status"] = -1
    
    def GetStatus(self):
        return self.agent["status"]
    
    def GetName(self):
        return self.agent["name"]

    def GetRole(self):
        return self.agent["role"]
    
    def DoPlanning(self, question_template, idx):
        self.DoMemory()
        self.DoReflect()
        question = question_template.format(self._playerInfoBuilder(), "", idx)
        if self.GM.god_instruct != "":
            question = self._playerInfoBuilder() + "." + self.GM.god_instruct
        
        answerapi = self.DoAnswer(question)
        self.DoAction(answerapi)
        pass
    
    # answering question
    def DoAnswer(self, question):
        Info("\t\t===== DoAnswer {0} {1} ======".format(self.GM.current_time,self.agent["name"]))
        answer = self._invoke(question)
        return answer
    
    def DoAnswerApi(self, question):
        Info("\t\t===== DoAnswerApi {0} {1} ======".format(self.GM.current_time,self.agent["name"]))
        output = self._invoke(question)
        Info("")
        answer = self._invokeAssistantApi(output["response"])
        return answer
    
    def DoAction(self, answer):
        Info("\t\t===== DoAction {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        if answer == "":
            return
        
        response = ParseJson(answer["response"])
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
    
    def AddMemory(self, memory):
        Debug(memory)
        output = game_config_dict["player"]["action_confirm"]
        self.agent["conversation"].memory.save_context({"input": memory}, {"ouput": output})
    
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
            self.AddMemory(summary['response'])
        pass
    
    def DoReflect(self, memorysize=20):
        if self.GM.quick:
            return
        Info("\t\t===== DoReflect {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        
        memories = self.agent["conversation"].memory.load_memory_variables({})
        if len(memories['chat_history']) == 0:
            return 
        
        for history in memories['chat_history'][-1*memorysize:]:
            Debug(history)
        
        question = game_config_dict["player"]["action_reflect"].format(self._playerInfoBuilder(), "")
        reflect = self.DoAnswer(question)
        Debug("\tREFLECT: " + reflect["response"])
        return reflect["response"]

    
