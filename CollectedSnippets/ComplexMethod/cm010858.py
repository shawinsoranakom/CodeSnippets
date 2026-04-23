def add_backward_args(self, ctx: Any, all_args: list[Any]) -> None:
        if self.num_rng == 0:
            return

        curr_backward_iter = ctx._curr_iter
        retain_graph = torch._C._autograd._get_current_graph_task_keep_graph()

        # Save current state if we have a pending forward that needs this state
        # or this state may be needed again because of retain graph
        if (
            self.backward_state_position in self.pending_forwards
            and self.backward_state_position not in self.saved_backward_tensor_states
            and (self.backward_state_position != curr_backward_iter or retain_graph)
        ):
            self.saved_backward_tensor_states[self.backward_state_position] = [
                rng_state.get_state() for rng_state in self.bwd_rng_states
            ]

        # Restore saved states if needed
        if curr_backward_iter in self.saved_backward_tensor_states:
            if self.backward_state_position != curr_backward_iter:
                for bwd_state, saved_state in zip(
                    self.bwd_rng_states,
                    self.saved_backward_tensor_states[curr_backward_iter],
                ):
                    bwd_state.set_state(saved_state)
            if not retain_graph:
                del self.saved_backward_tensor_states[curr_backward_iter]
        else:
            if self.backward_state_position != curr_backward_iter:
                raise AssertionError(
                    "expected backward_state_position == curr_backward_iter, "
                    f"got {self.backward_state_position} != {curr_backward_iter}"
                )

        self.backward_state_position = curr_backward_iter + 1
        if not retain_graph:
            self.pending_forwards.remove(curr_backward_iter)
        all_args.extend(self.bwd_rng_states)