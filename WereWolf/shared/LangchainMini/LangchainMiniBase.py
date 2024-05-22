from .LangChainMiniMemory import *

RETRY_NUM = 5

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
    
    def __init__(self, model_id):
        self.model_id = model_id
        self.display()
        pass
    
    def display(self):
        logger.info(f"Invoking: {self.model_id}")
        
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