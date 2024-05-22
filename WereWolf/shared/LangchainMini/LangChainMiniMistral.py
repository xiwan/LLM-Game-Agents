from .LangchainMiniBase import *

class Mistral7BBedrock(LLMProduct):

    def __init__(self, ak="", sk="", sts_token="", aws_region="us-east-1", model_id="mistral.mistral-7b-instruct-v0:2"):
        super().__init__(model_id)