from .LangchainMiniBase import *

class Anthropic2Bedrock(LLMProduct):
    def __init__(self):
        super().__init__("anthropic.claude-v2")
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


class Anthropic3Bedrock(LLMProduct):
    role = "user"
    assistant = "assistant"

    def __init__(self, ak="", sk="", sts_token="", aws_region="us-east-1", model_id="anthropic.claude-3-sonnet-20240229-v1:0"):
        super().__init__(model_id)
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
        message = {"role": self.role, "content": prompt}
        qapair = [message]
        messages = [message]

        if self.memory is None:
            messages = [message]
        else:
            if self.retry == RETRY_NUM:
                self._update(message)
            messages = self._recall()
        
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

        self._update(response)
        qapair.append(response)
        self.retry = RETRY_NUM
        return qapair