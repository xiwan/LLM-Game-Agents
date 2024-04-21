from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerProphet(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.checkList = {}

    def _getPlayerRole(self, name) -> str:
        for player in roles_dict["players"]:
            if player["name"] == name:
                return (name, player["role"])
                # return "{0}:{1}".format(name, player["role"])
        return (None, None)
    
    def _checkPlayer(self, action_time, name, role):
        # 检查当前轮数是否已经存在记录
        if action_time in self.checkList and self.checkList[action_time]:
            Info(f"Error: Round {action_time} already has a record {name}:{role}.")
            return False
        # 创建新的内层字典,并将玩家编号和身份存储进去
        self.checkList[action_time] = {name: role}
        Info(self.checkList)
        return True
    
    def DoMemory(self, memorysize=20, memories=[]):
        for log in self.GM.game_prophet_check_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))

        memories = super().DoMemory(memorysize, memories)
        return memories

    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay:
            return None

        if abilityName == "ProphetCheck":
            name, role= self._getPlayerRole(target)
            if name is None or role is None:
                return log
            
            if not self._checkPlayer(item["action_time"], name, role):
                return log
            
            # self.checkList.append(checker)
            checker = "{0}:{1}".format(name, role)
            self.GM.game_prophet_check_log.append(checker)
            log = ReadableActionLog("prophet_check_log", self.GM.current_time, self.agent, item)
        return log