def update_game_states(self):
        step_idx = self.step_idx % self.per_round_steps
        if step_idx not in [15, 18] or self.step_idx in self.eval_step_idx:
            return
        else:
            self.eval_step_idx.append(self.step_idx)  # record evaluation, avoid repetitive evaluation at the same step

        if step_idx == 15:  # step no
            # night ends: after all special roles acted, process the whole night
            self.player_current_dead = []  # reset

            if self.player_hunted != self.player_protected and not self.is_hunted_player_saved:
                self.player_current_dead.append(self.player_hunted)
            if self.player_poisoned:
                self.player_current_dead.append(self.player_poisoned)

            self._update_players_state(self.player_current_dead)
            # reset
            self.player_hunted = None
            self.player_protected = None
            self.is_hunted_player_saved = False
            self.player_poisoned = None
        elif step_idx == 18:
            # updated use vote_kill_someone
            pass