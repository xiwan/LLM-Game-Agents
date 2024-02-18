import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .GameAssistant import GameAssistant
from .AnthropicTokenCounter import AnthropicTokenCounter
from .PeTemplates import *

class GamePlayer:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, player, GM):
        
        claude_llm = Bedrock(
            model_id="anthropic.claude-v2",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            model_kwargs=inference_modifier,
        )
        self.token_counter = AnthropicTokenCounter(claude_llm)
        
        _template_role = template_role.replace("{nickname}", player["name"])
        _template_role = _template_role.replace("{role}", player["role"])
        _template_role = _template_role.replace("{character}", player["character"])
        
        #confirmed_role = confirmed_role.replace("{init_players}", GetAllPlayersName())
        # if player["role"] == "狼人":
        #     confirmed_role = confirmed_role.replace("{teammates}", GetAllWolvesName())
        # if player["role"] == "村民":
        #     confirmed_role = confirmed_role.replace("{teammates}", game_config_dict["player"]["action_villager_team"])

        _template_role_prompt = PromptTemplate.from_template(_template_role)
        #_template_role_prompt.format(nickname=player["name"], role=player["role"], character=player["character"])

        role_memory = ConversationBufferWindowMemory(k = 100, return_messages=True,
                                                     human_prefix="Human", ai_prefix="AI", 
                                                     memory_key="chat_history", input_key="input")

        player["conversation"] = ConversationChain(
            prompt=_template_role_prompt,
            llm=claude_llm, 
            verbose=False, 
            memory=role_memory
        )
        Debug(player["conversation"])
                
        self.GM = GM
        self.agent = player
        self.assistant = GameAssistant(template_assistant_role, 200, GM)
        pass
    
    def _invoke(self, question):
        Info("\tQUESTION: " + question)
        answer = self.agent["conversation"].invoke(input = question, config={"callbacks": [self.token_counter]})
        self.GM.input_tokens = self.GM.input_tokens + self.token_counter.input_tokens
        self.GM.output_tokens = self.GM.output_tokens + self.token_counter.output_tokens
        return answer
    
    def _invokeAssistant(self, question):
        teamexplain = "(初始配置为2狼人+6村民, 游戏每轮发言顺序为P1,P2,P3,P4,P5,P6,P7,P8)"
        boardInfo = "[目前场上信息:{0}{1}.] ".format(GetAllPlayersName(), teamexplain)
        question = boardInfo + question
        Debug("\tASSISTANT QUESTION : " + question)
        return self.assistant.DoAnswer(question)
    
    def _playerInfoBuilder(self):
        boardInfo = "目前场上玩家:{0}(逗号为分割符).".format(GetAllPlayersName())
        if self.agent["role"] == "狼人":
            playerInfo = "现在是{2},你是玩家{0}(狼人身份,本阵营为:{1}).{3}".format(self.agent["name"], GetAllWolvesName(), self.GM.current_time, boardInfo)
        if self.agent["role"] == "村民":
            playerInfo = "现在是{2},你是玩家{0}(村民身份).{1}.{3}".format(self.agent["name"], "", self.GM.current_time, boardInfo)
        return playerInfo
    
    def IsWolf(self):
        return self.GetRole() == "狼人"
    
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
        answer = self.DoAnswer(question)
        self.DoAction(answer)
        pass
    
    # answering question
    def DoAnswer(self, question):
        Info("\t===== DoAnswer {0} {1} ======".format(self.GM.current_time,self.agent["name"]))
        answer = self._invoke(question)
        return answer
    
    def DoAction(self, answer):
        Info("\t===== DoAction {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        if answer == "":
            return
        
        response = ParseJson(answer["response"])
        memories = []
        for res in response:
            res_obj = json.loads(res)
            log = ""
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
        Info("\t===== DoMemory {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        
        memories = []
        for log in self.GM.game_pulbic_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
            pass
        
        if self.IsWolf():
            for log in self.GM.game_wolf_vote_log[-1*memorysize:]:
                memories.append(json.dumps(log, ensure_ascii=False))
                pass
            
        if len(memories) > 0:
            summary = self._invokeAssistant(".".join(memories))
            self.AddMemory(summary['response'])
        pass
    
    def DoReflect(self, memorysize=20):
        Info("\t===== DoReflect {0} {1} ======".format(self.GM.current_time, self.agent["name"]))
        
        memories = self.agent["conversation"].memory.load_memory_variables({})
        if len(memories['chat_history']) == 0:
            return 
        
        for history in memories['chat_history'][-1*memorysize:]:
            Debug(history)
        
        question = game_config_dict["player"]["action_reflect"].format(self._playerInfoBuilder(), "")
        reflect = self.DoAnswer(question)
        Debug("\tREFLECT: " + reflect["response"])
        return reflect["response"]

    
