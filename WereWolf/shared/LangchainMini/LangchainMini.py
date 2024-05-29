from .LangchainMiniBase import *
from .LangChainMiniKlass import *
from .LangChainMiniClaude import *
from .LangChainMiniMistral import *
from .LangChainMiniLlama import *

class LangchainMini():
    
    def __init__(self, model_id, 
                 platform="bedrock", 
                 stream:bool=True, 
                 memory:LangchainMiniMemory=None,
                 message:bool=True,
                 maxtoken:int=2048,
                 termperature:float=0.8,
                 system:str=None):
        self.llm = None
        try:
            if model_id == "anthropic.claude-instant-v1":
                self.llm = Anthropic2Bedrock()
            elif model_id == "anthropic.claude-v2":
                self.llm = Anthropic2Bedrock()
            elif model_id == "anthropic.claude-3-sonnet-20240229-v1:0" or model_id == "anthropic.claude-3-haiku-20240307-v1:0" or model_id == "anthropic.claude-3-opus-20240229-v1:0":
                if platform == "bedrock":
                    self.llm = Anthropic3Bedrock(aws_region="us-east-1", model_id=model_id)
                else:
                    self.llm = Anthropic3(api_key="")
            elif model_id == "mistral.mixtral-8x7b-instruct-v0:1" or model_id == "mistral.mistral-7b-instruct-v0:2":
                self.llm = Mistral7BBedrock(aws_region="us-east-1", model_id=model_id)
            elif model_id == "meta.llama3-8b-instruct-v1:0" or model_id == "meta.llama3-70b-instruct-v1:0":
                self.llm = Llama8BBedrock(aws_region="us-east-1", model_id=model_id)
                pass
            
        except ClientError:
            logger.exception("Couldn't invoke model %s", model_id)
            raise
            
        self.llm.stream = stream
        if not memory is None:
            self.llm._memory(memory)
        if not system is None:
            self.llm._system(system)
        pass

    def invoke(self, prompt: str):
        if False and not self.llm.memory is None: 
            qapair = self.llm.memory.summerize()
            history = "" if qapair is None else qapair[1]
            prompt = LangchainMiniPromptTemplate(prompt).format(history=history, chat_history=history)
        # logger.info(prompt)
        return self.llm._invoke(prompt)
    
    def addMemory(self, memory: str):
        message = {"role": self.llm.role, "content": memory}
        self.llm._update(message)
        message = {"role": self.llm.assistant, "content": "ok"}
        self.llm._update(message)
        pass
    
    def clear(self):
        self.llm._clear()
        pass

        