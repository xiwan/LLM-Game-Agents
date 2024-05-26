from . import *
from .PeTemplates import *

class GameCandidates(object):
    
    def __init__(self, name):
        self.candidates = {}
        self.name = name

    def reset(self):
        for candidate in self.candidates:
            self.candidates[candidate] = 0
        Info("投票系统已重置。")
        
    def set(self, players):
        for player in players:
            self.add(player.GetName());
        
    def add(self, name):
        if not name in self.candidates:
            self.candidates[name] = 0
            Info(f"玩家 {name} 已成为投票 {self.name} 候选者。")

    def vote(self, candidate):
        if candidate in self.candidates:
            self.candidates[candidate] += 1
            Info(f"玩家 {candidate} 得票为:{self.count(candidate)}")
        else:
            Error(f"NOT VALID: {candidate}")
            
    def win(self):
        if self.nocandidate():
            Info("NO CANDIDATES")
            return None

        max_votes = max(self.candidates.values())
        winners = [candidate for candidate, votes in self.candidates.items() if votes == max_votes]

        if len(winners) == 1:
            Info(f"{self.name} BOARD WINNER: {winners[0]}, VOTES: {max_votes}")
        else:
            Info(f"{self.name} BOARD WINNERS: {', '.join(winners)}, VOTES: {max_votes}")

        return winners
    
    def nocandidate(self):
        return not self.candidates or len(self.candidates) == 0
    
    def getcandidate(self, roles_dict=[]):
        
        return [{"name": item["name"], "count": self.candidates[item["name"]], "id": item["id"]} for item in roles_dict]

        #return [{"name": name, "count": count} for name, count in self.candidates.items()] 
    
    def count(self, candidate):
        if candidate in self.candidates:
            return self.candidates[candidate]
        else:
            return None
    
@singleton
class GameVotes(object):
    
    def __init__(self, GM):
        self.GM = GM
        pass
    
    def WithPoisionVote(self, i, vote:GameCandidates):
        #vote.reset()
        #poision_names = []
        # logs = self.GM.game_witch_potion_log
        # for log in logs:
        #     # Witch Poision
        #     if (not isinstance(log, str)) and log["time"] == self.GM.current_time and EqualIgnoreCase(log["response"]["action"], "WitchPoision"):
        #         if log["response"]["target"] != "" :
        #             vote.vote(log["response"]["target"])
        if vote.nocandidate():
            return False
        
        self.GM.poisions = vote.win()
        vote.reset()
        target = self.GM.poisions[0]
        target_count = vote.count(target)
        Info(f"\t [NIGHT_WITCH] target={target}, count={target_count}")
        if target_count == 0:
            return True
        return self.EliminateOrRevivePlayer(target, "[NIGHT_WITCH]", "WitchPoision", 0)
    
    def WithAntidoteVote(self, i, vote:GameCandidates):
        #vote.reset()
        #antidote_names = []
        # logs = self.GM.game_witch_potion_log
        # for log in logs:
        #     # Witch WitchAntidote
        #     if (not isinstance(log, str)) and log["time"] == self.GM.current_time and EqualIgnoreCase(log["response"]["action"], "WitchAntidote"):
        #         if log["response"]["target"] != "" :
        #             vote.vote(log["response"]["target"])
        if vote.nocandidate():
            return False
        
        self.GM.antidotes = vote.win()
        vote.reset()
        target = self.GM.antidotes[0]
        target_count = vote.count(target)
        Info(f"\t [NIGHT_WITCH] target={target}, count={target_count}")
        if target_count == 0:
            return True
        return self.EliminateOrRevivePlayer(target, "[NIGHT_WITCH]", "WitchAntidote", 1)
    
    
    def MajorityVote(self, i, vote:GameCandidates):
        # vote.reset()
        # logs = self.GM.game_player_vote_log if self.GM.isDay else self.GM.game_wolf_vote_log
        # action = "playerVote" if self.GM.isDay else "wolfvote"
        # for log in logs:
        #     if (not isinstance(log, str)) and log["time"] == self.GM.current_time and EqualIgnoreCase(log["response"]["action"], action):
        #         if log["response"]["target"] != "" :
        #             vote.vote(log["response"]["target"])
        # if vote.nocandidate():
        #     return False
        
        if self.GM.isDay:
            return self.DayVote(i, vote)
        else:
            return self.NightVote(i, vote)
        pass

    def NightVote(self, i, vote:GameCandidates):

        self.GM.wolfvotes = vote.win()
        vote.reset()
        # not on agreement, need to share memory
        if len(self.GM.wolfvotes) != 1:
            for player in self.GM.player_agents:
                if player.IsWolf():
                    question = self.GM.Lang("system.wolf_vote_again").format(",".join(self.GM.wolfvotes))
                    Info("[NIGHT_VOTE_AGAIN]" + question)
                    self.GM.game_system_log.append(question)
                    self.GM.game_wolf_vote_log.append(question)
                    player.AddMemory(question)
            return False
                
        target = self.GM.wolfvotes[0]
        target_count = vote.count(target)
        Info(f"\t [NIGHT_VOTE] target={target}, count={target_count}")
        
        return self.EliminateOrRevivePlayer(target, "[NIGHT_VOTE]", "MasterVote", 0)
    
    def DayVote(self, i, vote:GameCandidates):
        
        self.GM.palyervotes = vote.win()
        vote.reset()
        if len(self.GM.palyervotes) != 1:
            for player in self.GM.player_agents:
                question = self.GM.Lang("system.player_vote_again").format(",".join(self.GM.palyervotes))
                Info("[DAY_VOTE_AGAIN]" + question)
                self.GM.game_system_log.append(question)
                self.GM.game_player_vote_log.append(question)
                player.AddMemory(question)
            return False
        
        target = self.GM.palyervotes[0]
        target_count = vote.count(target)
        Info(f"\t [DAY_VOTE] target={target}, count={target_count}")
        return self.EliminateOrRevivePlayer(target, "[DAY_VOTE]", "MasterVote", 0)

    def EliminateOrRevivePlayer(self, target, logTitle, langTitle, status=0):
        # kill the player and log it
        for player in self.GM.roles_dict["players"]:
            if EqualIgnoreCase(player["name"], target):
                Info("\t {0} player: {1} {2}".format(logTitle, player["name"], player["status"]))
                player["status"] = status # EliminateOrRevive !!!!
                Info("\t {0} player: {1} {2}".format(logTitle, player["name"], player["status"]))
                player_log = self.GM.Lang(langTitle).format(self.GM.current_time, player["name"])
                pub_log = ReadableActionLog(logTitle, self.GM.current_time, player["name"] , player_log)
                self.GM.game_public_log.append(pub_log)
                sys_log = SystemLog(logTitle, self.GM.current_time, player, player_log)
                self.GM.game_system_log.append(sys_log)
                return True
        return False