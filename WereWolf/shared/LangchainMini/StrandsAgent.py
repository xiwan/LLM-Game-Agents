from .LangChainMiniKlass import *
from strands import Agent, tool
from strands.models import BedrockModel

class StrandsAgent(LLMProduct):
    role = "user"
    assistant = "assistant"

    def __init__(self, 
        ak="", 
        sk="", 
        sts_token="", 
        aws_region="us-east-1", 
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0", 
        system_prompt = "",
        max_tokens=4096, temperature=0.8):

        super().__init__(model_id,max_tokens,temperature)
        self.streamtext = ""
        self.response = None
        self.stream = True

        bedrock_model = BedrockModel(
            model_id=self.model_id,
            region_name=aws_region,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        self.agent = Agent(
            system_prompt=system_prompt, 
            model=bedrock_model,
            callback_handler=self.callback_handler)
        pass
        
    def callback_handler(self, **kwargs):
        # Track event loop lifecycle
        if kwargs.get("init_event_loop", False):
            print("🔄 Event loop initialized")
        elif kwargs.get("start_event_loop", False):
            print("▶️ Event loop cycle starting")
        elif kwargs.get("start", False):
            print("📝 New cycle started")
        elif "message" in kwargs:
            print(f"📬 New message created, using model {self.model_id}")
            self.response = kwargs['message']
            self.streamtext = ""
        elif kwargs.get("complete", False):
            print("✅ Cycle completed")
        elif kwargs.get("force_stop", False):
            print(f"🛑 Event loop force-stopped: {kwargs.get('force_stop_reason', 'unknown reason')}")

        if "data" in kwargs:
            print(kwargs["data"], end='', flush=True)
            self.streamtext = self.streamtext + kwargs["data"]
        # if kwargs.get("complete", False):
        #     self.response = {"role": "assistant", "content": self.streamtext}
        #     print(self.response)
        #     self.streamtext = ""  # 重置streamtext为下一次使用
        pass
        
    def _invoke(self, prompt):
        if self.retry <= 0:
            logger.error("!!!retry failed!!!")
            return None
        # print(self.system)
        question = {"role": self.role, "content": prompt}
        messages = [question]

        if self.memory is None:
            messages = [question]
        else:
            if self.retry == RETRY_NUM:
                self._update(question)
            messages = self._recall()

        self.response = None  # 重置response
        self.agent(question["content"])

        # 等待complete事件发生
        while self.response is None:
            pass

        response = self.response
        self._update(response)
        self.retry = RETRY_NUM
        return [question, response]