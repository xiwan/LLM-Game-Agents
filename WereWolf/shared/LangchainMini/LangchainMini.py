import asyncio
import base64
import json
import logging
import os
import random
import numpy as np
import boto3
import time
from botocore.exceptions import ClientError
from anthropic import Anthropic,AnthropicBedrock
from abc import ABC, abstractmethod

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = logging.getLogger(__name__)

class LangchainMiniMemory():

    def __init__(self, k=0, llm=None):
        self.memories = []
        self.k = k*2+1
        self.llm =llm
        pass
    
    def history_old(self) -> str:
        memories = []
        for memory in self.memories[-1*self.k:]:
            memories.append(json.dumps(memory, ensure_ascii=False))
            pass
        return ".".join(memories)
    
    def historyStr(self) -> str:
        history = ""
        for memory in self.memories[-1*self.k:]:
            history = history + "{}:{}".format(memory["role"],memory["content"])
        return history
    
    def _update(self, memory, summary=False):
        #print("==========memory_update_start==========")
        self.memories.append(memory)
        if self.k > 0:
            self.memories = self.memories[-1*self.k:]
        #print(self.memories)
        #print("==========memory_update_end==========")
        return self.memories

    def clear(self):
        self.memories = []
    
    def summerize(self):
        if self.llm is None:
            return None
        
        content = self.historyStr()
        print(content)
        if len(content) > 0:
            _template = LangchainMiniPromptTemplate("{content}. 自然语言简洁总结,不超过{num}字, 需要保留关键信息，比如时间，玩家和动作.")
            num = min(len(self.memories[-1*self.k:])*15, 100)
            prompt = _template.format(content=content, num=num)
            
            print(prompt)
            print("-"*88)
            return self.llm._invoke(prompt)
        return None

class LLMInterface(ABC):
    @abstractmethod
    def _memory(self, memory:LangchainMiniMemory):
        pass
    
    @abstractmethod
    def _system(self, txt:str):
        pass
    
    @abstractmethod
    def _invoke(self, txt:str):
        pass

class LLMProduct():
    max_tokens = 2048
    temperature = 0.7
    system = ""
    memory = None
    
    def __init__(self, model_id):
        self.model_id = model_id
        self.display()
        pass
    
    def display(self):
        logger.info(f"Invoking: {self.model_id}")

            
class AnthropicBedrock2(LLMProduct, LLMInterface):
    def __init__(self):
        super().__init__("anthropic.claude-v2")
        pass 
    
    def _invoke(self, prompt):
        pass
    
    def _system(self, system):
        pass
        
class Anthropic3(LLMProduct, LLMInterface):
    messages = []
    
    def __init__(self, api_key):
        super().__init__("anthropic.claude-3-sonnet-20240229-v1:0")
        self.client = Anthropic(
            # This is the default and can be omitted
            api_key=api_key,
        )
        
    def _invoke(self, prompt):
        pass
    
    def _system(self, system):
        pass

RETRY_NUM = 5
class AnthropicBedrock3(LLMProduct, LLMInterface):
    role = "user"
    assistant = "assistant"
    retry = RETRY_NUM
        
    def __init__(self, ak="", sk="", sts_token="", aws_region="us-east-1"):
        super().__init__("anthropic.claude-3-sonnet-20240229-v1:0")
        self.client = AnthropicBedrock(
            # Authenticate by either providing the keys below or use the default AWS credential providers, such as
            # using ~/.aws/credentials or the "AWS_SECRET_ACCESS_KEY" and "AWS_ACCESS_KEY_ID" environment variables.
            aws_access_key=ak,
            aws_secret_key=sk,
            # Temporary credentials can be used with aws_session_token.
            # Read more at https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html.
            aws_session_token=sts_token,
            # aws_region changes the aws region to which the request is made. By default, we read AWS_REGION,
            # and if that's not present, we default to us-east-1. Note that we do not read ~/.aws/config for the region.
            aws_region=aws_region,
        )
    def _system(self, system):
        self.system = system
        pass
    
    def _memory(self, memory):
        self.memory = memory
        self.memory.llm = self
        pass
    
    def _invoke(self, prompt):
        if self.retry <= 0:
            logger.info("!!!retry failed!!!")
            return None
        # print(self.system)
        message = {"role": self.role, "content": prompt}
        qapair = [message]
        messages = [message]

        if self.memory is None:
            messages = [message]
        else:
            if self.retry == RETRY_NUM:
                messages = self.memory._update(message)
            else:
                messages = self.memory.memories
        
        response = None
        try:
            # if  self.retry == 5:
            #     raise Exception("exception...")
            if self.stream:
                with self.client.messages.stream(
                    model=self.model_id,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system,
                    messages=messages
                ) as stream:
                    streamtext = ""
                    for text in stream.text_stream:
                        print(text, end='', flush=True)
                        streamtext = streamtext + text
                    response = {"role": self.assistant, "content": streamtext}
            else:
                message = self.client.messages.create(
                    model=self.model_id,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system,
                    messages=messages
                )
                response = {"role": self.assistant, "content": message.content, "usage": message.usage}
        except Exception as e:
            logger.info(str(e))
            time.sleep(3)
            self.retry -= 1
            return self._invoke(prompt)
            
        qapair.append(response)
        if (not self.memory is None) and (not response is None):
            self.memory._update(response)
        self.retry = RETRY_NUM
        return qapair
        
class LangchainMiniPromptTemplate():
    template = ""
    
    def __init__(self, template):
        self.template = template
        pass
    
    def format(self, **kwargs):
        for key, value in kwargs.items():
            self.template = self.template.replace(f"{{{key}}}", str(value))
        return self.template

class LangchainMini():
    
    def __init__(self, model_id, 
                 platform="bedrock", 
                 stream:bool=True, 
                 memory:LangchainMiniMemory=None,
                 message:bool=True,
                 system:str=None):
        self.llm = None
        try:
            if model_id == "anthropic.claude-instant-v1":
                self.llm = AnthropicBedrock2()
            elif model_id == "anthropic.claude-v2":
                self.llm = AnthropicBedrock2()
            elif model_id == "anthropic.claude-3-sonnet-20240229-v1:0":
                if platform == "bedrock":
                    self.llm = AnthropicBedrock3(aws_region="us-east-1")
                else:
                    self.llm = Anthropic3(api_key="")
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
        self.llm.memory._update(message)
        message = {"role": self.llm.assistant, "content": "ok"}
        self.llm.memory._update(message)
    
    def clear(self):
        if not self.llm.memory is None:
            self.llm.memory.clear()

        