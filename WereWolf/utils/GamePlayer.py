import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .PeTemplates import *

class GamePlayer:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, player, GM):
        
        self.GM = GM
        
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

        role_memory = ConversationBufferWindowMemory(k = 27, return_messages=True,
                                                     human_prefix="Human", ai_prefix="AI", 
                                                     memory_key="chat_history", input_key="input")

        player["conversation"] = ConversationChain(
            prompt=_template_role_prompt,
            llm=claude_llm, 
            verbose=False, 
            memory=role_memory
        )
        
        self.agent = player  
        Debug(self.agent["conversation"])
        pass
    
    def _invoke(self, question):
        Info("\tQUESTION: " + question)
        return self.agent["conversation"].invoke(input = question)
    
    def _playerInfoBuilder(self):
        playerInfo = ""
        teamexplain = "(逗号为分割符)"
        if self.agent["role"] == "狼人":
            playerInfo = "你是玩家{0}(狼人身份,本阵营为:{1}).目前场上玩家状态:{2}{3}.".format(self.agent["name"], GetAllWolvesName(), GetAllPlayersName(), teamexplain)
        if self.agent["role"] == "村民":
            playerInfo = "你是玩家{0}(村民身份).{1}.目前场上玩家状态:{2}{3}.".format(self.agent["name"], "", GetAllPlayersName(), teamexplain)
        return playerInfo
    
    def Die(self):
        self.agent["status"] = -1
    
    def GetStatus(self):
        return self.agent["status"]
    
    def GetName(self):
        return self.agent["name"]

    def GetRole(self):
        return self.agent["role"]
    
    # answering question
    def DoAnswer(self, question):
        answer = self._invoke(question)
        return answer
    
    def DoAction(self, answer):
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
                    
                    #self.GM.game_memory_queue.put(log)
                pass
            memories.append(log)
        self.GM.game_system_log.append(SystemLog("[ROUND ACTION]", self.GM.current_time, self.agent, response))
        pass
    
    def DoMemory(self, memorysize=10):
        # memories = []
        # while self.game_memory_queue.qsize() > 0:
        #     memories.append(self.game_memory_queue.get(block=False))
        memories = []
        for log in self.GM.game_pulbic_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
            
        output = game_config_dict["player"]["action_confirm"]
        for memory in memories:
            self.agent["conversation"].memory.save_context({"input": memory}, {"ouput": output})
        pass
    
    def DoReflect(self):
        if not self.GM.isDay:
            return ""     
        # PlayersAllActions = []
        # for log in self.GM.game_pulbic_log:
        #     #if action["time"] == current_time:
        #     PlayersAllActions.append(json.dumps(log, ensure_ascii=False))
        
        memories = self.agent["conversation"].memory.load_memory_variables({})
        Debug(memories) 

        question = game_config_dict["player"]["action_reflect"].format(self._playerInfoBuilder(), "")
        reflect = self.DoAnswer(question)
        # parse LLM output
        if reflect != "":
            Debug("\tREFLECT: " + reflect["response"])
            return reflect["response"]
        return ""
        
    def DoPlanning(self, question_template, idx):
        # last 10 memories
        self.DoMemory(10)
        reflect = self.DoReflect()
        question = question_template.format(self._playerInfoBuilder(), reflect, idx)
        answer = self.DoAnswer(question)
        self.DoAction(answer)
        pass
    
