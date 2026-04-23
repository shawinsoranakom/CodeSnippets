def __iter__(self: AgentExecutorIterator) -> Iterator[AddableDict]:
        """Create an async iterator for the `AgentExecutor`."""
        logger.debug("Initialising AgentExecutorIterator")
        self.reset()
        callback_manager = CallbackManager.configure(
            self.callbacks,
            self.agent_executor.callbacks,
            self.agent_executor.verbose,
            self.tags,
            self.agent_executor.tags,
            self.metadata,
            self.agent_executor.metadata,
        )
        run_manager = callback_manager.on_chain_start(
            dumpd(self.agent_executor),
            self.inputs,
            self.run_id,
            name=self.run_name,
        )
        try:
            while self.agent_executor._should_continue(  # noqa: SLF001
                self.iterations,
                self.time_elapsed,
            ):
                # take the next step: this plans next action, executes it,
                # yielding action and observation as they are generated
                next_step_seq: NextStepOutput = []
                for chunk in self.agent_executor._iter_next_step(  # noqa: SLF001
                    self.name_to_tool_map,
                    self.color_mapping,
                    self.inputs,
                    self.intermediate_steps,
                    run_manager,
                ):
                    next_step_seq.append(chunk)
                    # if we're yielding actions, yield them as they come
                    # do not yield AgentFinish, which will be handled below
                    if self.yield_actions:
                        if isinstance(chunk, AgentAction):
                            yield AddableDict(actions=[chunk], messages=chunk.messages)
                        elif isinstance(chunk, AgentStep):
                            yield AddableDict(steps=[chunk], messages=chunk.messages)

                # convert iterator output to format handled by _process_next_step_output
                next_step = self.agent_executor._consume_next_step(next_step_seq)  # noqa: SLF001
                # update iterations and time elapsed
                self.update_iterations()
                # decide if this is the final output
                output = self._process_next_step_output(next_step, run_manager)
                is_final = "intermediate_step" not in output
                # yield the final output always
                # for backwards compat, yield int. output if not yielding actions
                if not self.yield_actions or is_final:
                    yield output
                # if final output reached, stop iteration
                if is_final:
                    return
        except BaseException as e:
            run_manager.on_chain_error(e)
            raise

        # if we got here means we exhausted iterations or time
        yield self._stop(run_manager)