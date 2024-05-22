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
from abc import ABC, abstractmethod
from anthropic import Anthropic,AnthropicBedrock

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = logging.getLogger(__name__)

class LangchainMiniMemory():

    def __init__(self, k=0, llm=None):
        self.memories = []
        self.k = k*2+1
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
    
    def update(self, memory, summary=False):
        #print("==========memory_update_start==========")
        self.memories.append(memory)
        if self.k > 0:
            self.memories = self.memories[-1*self.k:]
        #print(self.memories)
        #print("==========memory_update_end==========")
        return self.memories

    def clear(self):
        self.memories = []
    
#     def summerize(self):
#         if self.llm is None:
#             return None
        
#         content = self.historyStr()
#         print(content)
#         if len(content) > 0:
#             _template = LangchainMiniPromptTemplate("{content}. 自然语言简洁总结,不超过{num}字, 需要保留关键信息，比如时间，玩家和动作.")
#             num = min(len(self.memories[-1*self.k:])*15, 100)
#             prompt = _template.format(content=content, num=num)
            
#             print(prompt)
#             print("-"*88)
#             return self.llm._invoke(prompt)
#         return None