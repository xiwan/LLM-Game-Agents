import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .PeTemplates import *


class GameAssistant:
    global game_config_dict, roles_dict, template_player_role, claude_llm
    
    def __init__(self, template_role, GM):
        # Info(template_role)
        _template_role_prompt = PromptTemplate.from_template(template_role)
        role_memory = ConversationBufferWindowMemory(k = 1, return_messages=True,
                                                     human_prefix="Human", ai_prefix="AI", 
                                                     memory_key="chat_history", input_key="input")
        self.agent = ConversationChain(
            prompt=_template_role_prompt,
            llm=claude_llm, 
            verbose=False, 
            memory=role_memory
        )
        Debug(self.agent)
        self.GM = GM
        self.token_counter = self.GM.token_counter# AnthropicTokenCounter(claude_llm)
        pass
    
    def _invoke(self, question):
        answer = self.agent.invoke(input = question, config={"callbacks": [self.token_counter]})
        self.GM.input_tokens = self.GM.input_tokens + self.token_counter.input_tokens
        self.GM.output_tokens = self.GM.output_tokens + self.token_counter.output_tokens
        return answer
    
    # answering question
    def DoAnswer(self, question):
        return self._invoke(question)