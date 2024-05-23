from .LangChainMiniKlass import *
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

class Mistral7BBedrock(LLMProduct):

    def __init__(self, ak="", sk="", sts_token="", aws_region="us-east-1", 
                 model_id="mistral.mistral-7b-instruct-v0:2",
                 max_tokens=2048, temperature=0.8):
        super().__init__(model_id, max_tokens, temperature)
        
        self.bedrock = boto3.client(service_name="bedrock", region_name=aws_region)
        self.bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=aws_region)
        
        body = {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature #Temperature controls randomness; higher values increase diversity, lower values boost predictability.
        }
        
        def _invoke(self, prompt):
            
            instruction = f"<s>[INST] {prompt} [/INST]"
            body["prompt"] = instruction
            
            try:
                if self.stream:
                    pass
                else:
                    pass
                
                response = self.bedrock_runtime.invoke_model(
                    body=json.dumps(body),
                    modelId=self.model_id,
                    # You can replace above model with meta.llama2-13b-chat-v1 also
                    accept="application/json", 
                    contentType="application/json"
                )

            except Exception as e:
                logger.error(str(e))
                time.sleep(3)
                self.retry -= 1
                return self._invoke(prompt)

            pass
