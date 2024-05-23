from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerWolf(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)

    def _playerInfoBuilder(self):
        extraInfo = self.GM.Lang("wolfInfoBuilder").format(
            GetPartySize(self.GM.roles_dict, self.GM.lang), 
            GetAllWolvesName(self.GM.roles_dict, self.GM.lang))
        playerInfo = self.GM.game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo
    
    def DoMemory(self, memorysize=10, memories=[]):
        for log in self.GM.game_wolf_vote_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
        memories = super().DoMemory(memorysize, memories)

        return memories
    
    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay or target is None:
            return None

        if abilityName.lower().startswith('wolfvote'):
            log = ActionLog("wolf_vote_log", self.GM.current_time, self.agent, item)
            self.GM.game_wolf_vote_log.append(log)
            log = ReadableActionLog("wolf_vote_log", self.GM.current_time, self.agent["name"], item)
        return log