from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerWitch(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.inventory = []
            
    def _getItem(self, idx):
        return self.inventory[idx]
            
    def _useItem(self, idx): 
        assert self._getItem(idx) > 0, "item {0} empty".format(idx)
         # 0 poision 1 antidote
        self.inventory[idx] = max(0, min(self.inventory[idx], self.inventory[idx]-1))
    
    def _playerInfoBuilder(self):
        extraInfo = "药水道具状态: 毒药{0},解药{1}. ".format(self._getItem(0), self._getItem(1))
        playerInfo = game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo 
    
    def RefreshInventory(self):
        self.inventory = [1, 1] # 0 poision 1 antidote
        
    def UsePoision(self):
        self._useItem(0)
        
    def UseAntidote(self):
        self._useItem(1)
        
    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay:
            return None

        if abilityName == "WitchPoision":
            self.UsePoision()
            log = ReadableActionLog("witch_poision_log", self.GM.current_time, self.agent, item)

        if abilityName == "WitchAntidote":
            self.UseAntidote()
            log = ReadableActionLog("witch_antidote_log", self.GM.current_time, self.agent, item)
            
        return log