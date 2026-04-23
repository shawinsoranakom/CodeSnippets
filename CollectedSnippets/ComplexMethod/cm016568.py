def prepare_current_keyframe(self, curr_t: float, transformer_options: dict[str, torch.Tensor]) -> bool:
        if self.is_empty():
            return False
        if curr_t == self._curr_t:
            return False
        max_sigma = torch.max(transformer_options["sample_sigmas"])
        prev_index = self._current_index
        prev_strength = self._current_strength
        # if met guaranteed steps, look for next keyframe in case need to switch
        if self._current_used_steps >= self._current_keyframe.get_effective_guarantee_steps(max_sigma):
            # if has next index, loop through and see if need to switch
            if self.has_index(self._current_index+1):
                for i in range(self._current_index+1, len(self.keyframes)):
                    eval_c = self.keyframes[i]
                    # check if start_t is greater or equal to curr_t
                    # NOTE: t is in terms of sigmas, not percent, so bigger number = earlier step in sampling
                    if eval_c.start_t >= curr_t:
                        self._current_index = i
                        self._current_strength = eval_c.strength
                        self._current_keyframe = eval_c
                        self._current_used_steps = 0
                        # if guarantee_steps greater than zero, stop searching for other keyframes
                        if self._current_keyframe.get_effective_guarantee_steps(max_sigma) > 0:
                            break
                    # if eval_c is outside the percent range, stop looking further
                    else:
                        break
        # update steps current context is used
        self._current_used_steps += 1
        # update current timestep this was performed on
        self._curr_t = curr_t
        # return True if keyframe changed, False if no change
        return prev_index != self._current_index and prev_strength != self._current_strength