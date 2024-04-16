from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .GameAssistant import GameAssistant
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerWitch(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.inventory = []
            
    def _getItem(self, idx):
        if self.IsWitch():
            return self.inventory[idx]
        return -1
            
    def _useItem(self, idx): 
        if self.IsWitch(): # 0 poision 1 antidote
            self.inventory[idx] = max(0, min(self.inventory[idx], self.inventory[idx]-1))
            
    def _stateInfoBuilder(self):
        boardInfo = super()._stateInfoBuilder()
        boardInfo += "药水道具状态:毒药{0},解药{1}.".format(self._getItem(0), self._getItem(1))
        return boardInfo
    
    def RefreshInventory(self):
        self.inventory = [1, 1] # 0 poision 1 antidote