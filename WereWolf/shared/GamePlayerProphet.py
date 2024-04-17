from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerProphet(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.checkList = []

    def _getPlayerRole(self, name) -> str:
        for player in roles_dict["players"]:
            if player["name"] == name:
                return "{0}:{1}".format(name, player["role"])
        return None
    
    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay:
            return None
        
        checker = self._getPlayerRole(target)
        Info(checker)
        if checker is None:
            return None

        if abilityName == "ProphetCheck":
            self.checkList.append(checker)
            self.GM.game_prophet_check_log.append(checker)
            log = ReadableActionLog("prophet_check_log", self.GM.current_time, self.agent, item)
        return log