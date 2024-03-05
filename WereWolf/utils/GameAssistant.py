import json,time
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .PeTemplates import *


class GameAssistant:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, GM):
        self.GM = GM
        # Info(template_role)
        _template_role_prompt = PromptTemplate.from_template(template_role)
        role_memory = ConversationBufferWindowMemory(k = 1, return_messages=True,
                                                     human_prefix="Human", ai_prefix="Assistant", 
                                                     memory_key="chat_history", input_key="input")
        self.agent = ConversationChain(
            prompt=_template_role_prompt,
            llm=self.GM.llm, 
            verbose=False, 
            memory=role_memory
        )
        Debug(self.agent)
        self.token_counter = self.GM.token_counter# AnthropicTokenCounter(claude_llm)
        pass
    
    def _invoke(self, question):
        time.sleep(500 / 1000)
        answer = self.agent.invoke(input = question, config={"callbacks": [self.token_counter]})
        self.GM.input_tokens = self.GM.input_tokens + self.token_counter.input_tokens
        self.GM.output_tokens = self.GM.output_tokens + self.token_counter.output_tokens
        return answer
    
    # answering question
    def DoAnswer(self, question):
        return self._invoke(question)