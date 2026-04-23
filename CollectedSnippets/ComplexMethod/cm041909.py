def _check_game_finish(self) -> bool:
        """return True if game finished else False"""
        # game's termination condition
        terminated = False
        living_werewolf = [p for p in self.werewolf_players if p in self.living_players]
        living_villagers = [p for p in self.villager_players if p in self.living_players]
        living_special_roles = [p for p in self.special_role_players if p in self.living_players]
        if not living_werewolf:
            self.winner = "good guys"
            self.win_reason = "werewolves all dead"
            terminated = True
        elif not living_villagers or not living_special_roles:
            self.winner = "werewolf"
            self.win_reason = "villagers all dead" if not living_villagers else "special roles all dead"
            terminated = True
        return terminated