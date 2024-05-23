from .LangchainMiniBase import *

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
        #return self.memories
        pass

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


class LLMInterface(ABC):
    @abstractmethod
    def _memory(self, memory:LangchainMiniMemory):
        pass
    
    @abstractmethod
    def _recall(self):
        pass
    
    @abstractmethod
    def _system(self, txt:str):
        pass
    
    @abstractmethod
    def _invoke(self, txt:str):
        pass
    
    @abstractmethod
    def _update(self, txt:str):
        pass
    
    @abstractmethod
    def _clear(self):
        pass
    
    @abstractmethod
    def _summary(self):
        pass

class LangchainMiniPromptTemplate():
    template = ""
    
    def __init__(self, template):
        self.template = template
        pass
    
    def format(self, **kwargs):
        for key, value in kwargs.items():
            self.template = self.template.replace(f"{{{key}}}", str(value))
        return self.template

class LLMProduct(LLMInterface):
    max_tokens = 2048
    temperature = 0.8
    system = ""
    memory = None
    
    retry = RETRY_NUM
    
    def __init__(self, model_id, max_tokens=2048, temperature=0.8):
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.display()
        pass
    
    def display(self):
        logger.info(f"model_id: {self.model_id}, max_tokens:{self.max_tokens}, temperature:{self.temperature}")
        
    def _system(self, system):
        self.system = system
        pass
    
    def _memory(self, memory):
        self.memory = memory
        pass
    
    def _invoke(self, prompt):
        pass
    
    def _update(self, memory):
        if (not self.memory is None) and (not memory is None):
            self.memory.update(memory)
        pass

    def _clear(self):
        if (not self.memory is None):
            self.memory.clear()
        pass
    
    def _recall(self):
        if (not self.memory is None):
            return self.memory.memories
        else:
            return None
        
    def _summary(self):
        pass