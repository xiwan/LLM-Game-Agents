from langchain.prompts import PromptTemplate
import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .PeTemplates import *

class GamePlayer:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, player, GM):
        
        self.GM = GM
        
        confirmed_role = template_role.replace("{nickname}", player["name"])
        confirmed_role = confirmed_role.replace("{role}", player["role"])
        confirmed_role = confirmed_role.replace("{character}", player["character"])
        
        #confirmed_role = confirmed_role.replace("{init_players}", GetAllPlayersName())
        # if player["role"] == "狼人":
        #     confirmed_role = confirmed_role.replace("{teammates}", GetAllWolvesName())
        # if player["role"] == "村民":
        #     confirmed_role = confirmed_role.replace("{teammates}", game_config_dict["player"]["action_villager_team"])

        prompt_role = PromptTemplate.from_template(confirmed_role)
        prompt_role.format(chat_history="", input="")

        role_memory = ConversationBufferWindowMemory(k = 20, ai_prefix="AI Assistant", memory_key="chat_history", input_key="input")
        
        # Construct the ReAct agent
        # initialize agent with tools
        # player["conversation"] = initialize_agent(
        #     agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        #     tools=tools,
        #     llm=claude_llm,
        #     verbose=False,
        #     max_iterations=3,
        #     early_stopping_method='generate',
        #     memory=role_memory
        # )
        #agent = create_react_agent(claude_llm, tools, prompt_role)
        #player["agent_executor"] = AgentExecutor(agent=agent, tools=tools, verbose=False, memory=memory)

        player["conversation"] = ConversationChain(
            prompt=prompt_role,
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
        for res in response:
            res_obj = json.loads(res)

            if res_obj["action"] == "WolfVote":
                if not self.GM.isDay:
                    log = ActionLog("wolf_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_wolf_vote_log.append(log)
                pass
                
            if res_obj["action"] == "PlayerVote":
                if self.GM.isDay:
                    log = ActionLog("player_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_vote_log.append(log)
                    log = ReadableActionLog("player_vote_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                pass
            
            if res_obj["action"] == "Debate":
                if self.GM.isDay:
                    log = ActionLog("player_debate_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_action_log.append(log)
                    log = ReadableActionLog("player_debate_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                pass

            if res_obj["action"] == "GetAllPlayersName":
                memory = game_config_dict["system"]["board"].format(GetAllPlayersName())
                self.DoMemory(memory)
                
                log = ActionLog("player_check_log", self.GM.current_time, self.agent, res_obj)
                self.GM.game_player_action_log.append(log)
                pass
                
            if res_obj["action"] == "DeathWords":
                if self.GM.isDay:
                    log = ActionLog("player_deathwords_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_player_action_log.append(log)
                    log = ReadableActionLog("player_deathwords_log", self.GM.current_time, self.agent, res_obj)
                    self.GM.game_pulbic_log.append(log)
                pass
        
        self.GM.game_system_log.append(SystemLog("[ROUND ACTION]", self.GM.current_time, self.agent, response))
        pass
    
    def DoMemory(self, memory):
        output = game_config_dict["player"]["action_confirm"]
        self.agent["conversation"].memory.save_context({"input": memory}, {"ouput": output})
        pass
    
    def DoReflect(self):
        if not self.GM.isDay:
            return ""     
        PlayersAllActions = []
        for log in self.GM.game_pulbic_log:
            #if action["time"] == current_time:
            PlayersAllActions.append(json.dumps(log, ensure_ascii=False))
            
        context = ""
        if len(PlayersAllActions) > 0:
            context = "日志为:"+" ".join(PlayersAllActions) + ".根据日志进行局面分析."
            
        question = game_config_dict["player"]["action_reflect"].format(self._playerInfoBuilder(), context)
        reflect = self.DoAnswer(question)
        # parse LLM output
        if reflect != "":
            Debug("\tREFLECT: " + reflect["response"])
            return reflect["response"]
        return ""
        
    def DoPlanning(self, question_template, idx):
        reflect = self.DoReflect()
        question = question_template.format(self._playerInfoBuilder(), reflect, idx)
        answer = self.DoAnswer(question)
        self.DoAction(answer)
        pass
    
    def _playerInfoBuilder(self):
        playerInfo = ""
        teamexplain = "(逗号为分割符，分割后每个单元由 名字:状态(1表示存活, 0/-1表示死亡) 组成)"
        if self.agent["role"] == "狼人":
            playerInfo = "你是玩家{0},身份为狼人,狼人包括:{1}.目前场上玩家状态:{2}{3}.".format(self.agent["name"], GetAllWolvesName(), GetAllPlayersName(), teamexplain)
        if self.agent["role"] == "村民":
            playerInfo = "你是玩家{0},身份为村民.{1}目前场上玩家状态:{2}{3}.".format(self.agent["name"], "", GetAllPlayersName(), teamexplain)
        return playerInfo