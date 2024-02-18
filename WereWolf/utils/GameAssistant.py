import json
from . import ParseJson, print_ww, Print, Info, Debug, Warn, Error
from .PeTemplates import *


class GameAssistant:
    global game_config_dict, roles_dict, template_player_role
    
    def __init__(self, template_role, num):
        _template_role = template_role.replace("{num}", str(num))
        _template_role_prompt = PromptTemplate.from_template(_template_role)
        
        claude_llm = Bedrock(
            model_id="anthropic.claude-v2",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            model_kwargs=inference_modifier,
        )
        
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

        pass
    
    def _invoke(self, question):
        return self.agent.invoke(input = question)
    
    # answering question
    def DoAnswer(self, question):
        return self._invoke(question)