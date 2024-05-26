from . import *
from .PeTemplates import *
from .GamePlayer import GamePlayer
from .LangchainMini.LangchainMini import LangchainMini, LangchainMiniMemory, LangchainMiniPromptTemplate

class GamePlayerWitch(GamePlayer):
    
    def __init__(self, player, GM):
        super().__init__(player, GM)
        self.inventory = [1, 1]# 0 poision 1 antidote
            
    def _getItem(self, idx):
        return self.inventory[idx]
            
    def _useItem(self, idx): 
        if self._getItem(idx) == 0:
            Info("potion {0} empty".format(idx))
            return False
        # assert self._getItem(idx) > 0, "item {0} empty".format(idx)
        # 0 poision 1 antidote
        self.inventory[idx] = max(0, min(self.inventory[idx], self.inventory[idx]-1))
        return True
    
    def _playerInfoBuilder(self):
        extraInfo = self.GM.Lang("witchInfoBuilder").format(self._getItem(0), self._getItem(1), self.GM.current_time)
        extraInfo += self.GM.Lang("playerInfoBuilder").format(GetPartySize(self.GM.roles_dict, self.GM.lang))
        #playerInfo = self.GM.game_config_dict["player"]["action_prefix"].format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        playerInfo = self.GM.Lang("player.action_prefix").format(self.GetName(), self.GetRole(), self.GetCharacter(), extraInfo)
        return playerInfo
        
    def UsePoision(self):
        return self._useItem(0)
        
    def UseAntidote(self):
        return self._useItem(1)
    
    def DoMemory(self, memorysize=10, memories=[]):
        
        for log in self.GM.game_witch_potion_log[-1*memorysize:]:
            memories.append(json.dumps(log, ensure_ascii=False))
        memories = super().DoMemory(memorysize, memories)
        return memories

    def UsePlayerAbility(self, abilityName, target=None, item=None):
        log = super().UsePlayerAbility(abilityName, target, item)
        if self.GM.isDay or target is None:
            return None
        # Poision
        if EqualIgnoreCase(abilityName, "WitchPoision"):
            if self.UsePoision():
                log = ActionLog("witch_poision_log", self.GM.current_time, self.agent, item)
                self.GM.game_witch_potion_log.append(log)
                player_log =  self.GM.Lang("WitchPoision").format(self.GM.current_time, target)
                log = ReadableActionLog("[WITCH POISION]", self.GM.current_time, target, player_log)
                self.GM.game_public_log.append(log)
                self.AddMemory(log)
                self.GM.witchPoisionVotes[-1].vote(target)
                
        # Antidote
        if EqualIgnoreCase(abilityName, "WitchAntidote"):
            if self.UseAntidote():
                log = ActionLog("witch_antidote_log", self.GM.current_time, self.agent, item)
                self.GM.game_witch_potion_log.append(log)
                player_log =  self.GM.Lang("WitchAntidote").format(self.GM.current_time, target)
                log = ReadableActionLog("[WITCH ANTIDOTE]", self.GM.current_time, target, player_log)
                self.GM.game_public_log.append(log)
                self.AddMemory(log)
                self.GM.witchAntiDoteVotes[-1].vote(target)
        return log