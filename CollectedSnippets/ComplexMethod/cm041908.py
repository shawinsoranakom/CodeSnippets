def step(self, action: EnvAction) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        action_type = action.action_type
        player_name = action.player_name
        target_player_name = action.target_player_name
        if action_type == EnvActionType.WOLF_KILL:
            self.wolf_kill_someone(wolf_name=player_name, player_name=target_player_name)
        elif action_type == EnvActionType.VOTE_KILL:
            self.vote_kill_someone(voter_name=player_name, player_name=target_player_name)
        elif action_type == EnvActionType.WITCH_POISON:
            self.witch_poison_someone(witch_name=player_name, player_name=target_player_name)
        elif action_type == EnvActionType.WITCH_SAVE:
            self.witch_save_someone(witch_name=player_name, player_name=target_player_name)
        elif action_type == EnvActionType.GUARD_PROTECT:
            self.guard_protect_someone(guard_name=player_name, player_name=target_player_name)
        elif action_type == EnvActionType.PROGRESS_STEP:
            self.progress_step()
        elif action_type == EnvActionType.NONE:
            pass
        else:
            raise ValueError(f"not supported action_type: {action_type}")

        self.update_game_states()
        terminated = self._check_game_finish()
        obs = self._get_obs()
        return obs, 1.0, terminated, False, {}