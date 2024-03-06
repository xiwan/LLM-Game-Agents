from . import *
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GameAssistant:
    global game_config_dict, roles_dict
    
    def __init__(self, template_role, GM):
        self.GM = GM
        # logger.info(template_role)
        self.template_role = LangchainMiniPromptTemplate(template_role)
        
        role_memory = LangchainMiniMemory(k=1)
        self.agent = LangchainMini(model_id="anthropic.claude-3-sonnet-20240229-v1:0", stream=True, memory=role_memory)

        pass
    
    def _invoke(self, question):
        _question = self.template_role.format(input=question)
        answer = self.agent.invoke(_question)
        # self.GM.input_tokens = self.GM.input_tokens + self.token_counter.input_tokens
        # self.GM.output_tokens = self.GM.output_tokens + self.token_counter.output_tokens
        return answer
    
    # answering question
    def DoAnswer(self, question):
        return self._invoke(question)