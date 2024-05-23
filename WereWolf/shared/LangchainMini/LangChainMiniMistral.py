from .LangChainMiniKlass import *
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class Mistral7BBedrock(LLMProduct):
    role = "user"
    assistant = "assistant"

    def __init__(self, ak="", sk="", sts_token="", aws_region="us-east-1", 
                 model_id="mistral.mistral-7b-instruct-v0:2",
                 max_tokens=2048, temperature=0.8):
        super().__init__(model_id, max_tokens, temperature)

        self.chat = ChatBedrock(
            model_id=self.model_id,
            model_kwargs={"temperature": self.temperature, "max_tokens": self.max_tokens},
        )
        pass

    def _invoke(self, prompt):
        if self.retry <= 0:
            logger.error("!!!retry failed!!!")
            return None
        
        question = {"role": self.role, "content": prompt}
        messages = [question]

        if self.memory is None:
            messages = [question]
        else:
            if self.retry == RETRY_NUM:
                self._update(question)
            messages = self._recall()
        
        _messages = []
        for msg in messages:
            if msg["role"] == self.role:
                _messages.append(HumanMessage(content=msg["content"]))
            if msg["role"] == self.assistant:
                _messages.append(AIMessage(content=msg["content"]))
            pass

        response = None
        try:
            systemMsg = SystemMessage(content=self.system)
            prompt = ChatPromptTemplate.from_messages(
                [
                    systemMsg,
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            chain = prompt | self.chat
            if self.stream:
                streamtext = ""
                for chunk in self.chat.stream(_messages):
                    print(chunk.content, end="", flush=True)
                    streamtext = streamtext + chunk.content
                response = {"role": self.assistant, "content": streamtext}
            else:
                message = self.chat.invoke(_messages)
                response = {"role": self.assistant, "content": message.content}
        except Exception as e:
            logger.error(str(e))
            time.sleep(3)
            self.retry -= 1
            return self._invoke(prompt)

        self._update(response)
        self.retry = RETRY_NUM
        return [question, response]
