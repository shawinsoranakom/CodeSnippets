async def _think(self) -> bool:
        """Consider what to do and decide on the next course of action. Return false if nothing can be done."""
        if len(self.actions) == 1:
            # If there is only one action, then only this one can be performed
            self._set_state(0)

            return True

        if self.recovered and self.rc.state >= 0:
            self._set_state(self.rc.state)  # action to run from recovered state
            self.recovered = False  # avoid max_react_loop out of work
            return True

        if self.rc.react_mode == RoleReactMode.BY_ORDER:
            if self.rc.max_react_loop != len(self.actions):
                self.rc.max_react_loop = len(self.actions)
            self._set_state(self.rc.state + 1)
            return self.rc.state >= 0 and self.rc.state < len(self.actions)

        prompt = self._get_prefix()
        prompt += STATE_TEMPLATE.format(
            history=self.rc.history,
            states="\n".join(self.states),
            n_states=len(self.states) - 1,
            previous_state=self.rc.state,
        )

        next_state = await self.llm.aask(prompt)
        next_state = extract_state_value_from_output(next_state)
        logger.debug(f"{prompt=}")

        if (not next_state.isdigit() and next_state != "-1") or int(next_state) not in range(-1, len(self.states)):
            logger.warning(f"Invalid answer of state, {next_state=}, will be set to -1")
            next_state = -1
        else:
            next_state = int(next_state)
            if next_state == -1:
                logger.info(f"End actions with {next_state=}")
        self._set_state(next_state)
        return True