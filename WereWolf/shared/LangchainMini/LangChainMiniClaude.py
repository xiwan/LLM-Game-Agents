from .LangChainMiniKlass import *
from anthropic import Anthropic,AnthropicBedrock
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from strands import Agent, tool
from strands.models import BedrockModel

class Anthropic2Bedrock(LLMProduct):
    def __init__(self,  model_id="anthropic.claude-v2"):
        super().__init__(model_id)
        pass 
    
    def _invoke(self, prompt):
        pass

class Anthropic3(LLMProduct):
    def __init__(self, api_key, model_id="anthropic.claude-3-sonnet-20240229-v1:0"):
        super().__init__(model_id)
        self.client = Anthropic(
            # This is the default and can be omitted
            api_key=api_key,
        )
        
    def _invoke(self, prompt):
        pass


class Anthropic3Strands(LLMProduct):
    role = "user"
    assistant = "assistant"

    def __init__(self, 
        ak="", sk="", sts_token="", aws_region="us-east-1", 
        model_id="anthropic.claude-3-sonnet-20240229-v1:0", 
        system_prompt = "",
        max_tokens=2048, temperature=0.8):
        super().__init__(model_id,max_tokens,temperature)

        self.streamtext = ""
        self.response = None
        self.stream = True

        bedrock_model = BedrockModel(
            model_id=self.model_id,
            region_name='us-east-1',
            temperature=0.7,
        )

        self.agent = Agent(
            system_prompt=system_prompt, 
            model=bedrock_model,
            callback_handler=self.callback_handler)
        
    def callback_handler(self, **kwargs):
        # Track event loop lifecycle
        if kwargs.get("init_event_loop", False):
            print("🔄 Event loop initialized")
        elif kwargs.get("start_event_loop", False):
            print("▶️ Event loop cycle starting")
        elif kwargs.get("start", False):
            print("📝 New cycle started")
        elif "message" in kwargs:
            print(f"📬 New message created")
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


class Anthropic3Bedrock(LLMProduct):
    role = "user"
    assistant = "assistant"

    def __init__(self, 
                 ak="", sk="", sts_token="", aws_region="us-east-1", 
                 model_id="anthropic.claude-3-sonnet-20240229-v1:0", 
                 max_tokens=2048, temperature=0.8):
        super().__init__(model_id,max_tokens,temperature)
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
        
        response = None
        try:
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
            logger.error(str(e))
            time.sleep(3)
            self.retry -= 1
            return self._invoke(prompt)

        self._update(response)
        self.retry = RETRY_NUM
        return [question, response]