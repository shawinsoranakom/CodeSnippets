def end_delegate(self) -> None:
        """Ends the currently active delegate (e.g., if it is finished or errored).

        so that this controller can resume normal operation.
        """
        if self.delegate is None:
            return

        delegate_state = self.delegate.get_agent_state()

        # update iteration that is shared across agents
        self.state.iteration_flag.current_value = (
            self.delegate.state.iteration_flag.current_value
        )

        # Calculate delegate-specific metrics before closing the delegate
        delegate_metrics = self.state.get_local_metrics()
        logger.info(f'Local metrics for delegate: {delegate_metrics}')

        # close the delegate controller before adding new events
        asyncio.get_event_loop().run_until_complete(self.delegate.close())

        if delegate_state in (AgentState.FINISHED, AgentState.REJECTED):
            # retrieve delegate result
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )

            # prepare delegate result observation
            # TODO: replace this with AI-generated summary (#2395)
            # Filter out metrics from the formatted output to avoid clutter
            display_outputs = {
                k: v for k, v in delegate_outputs.items() if k != 'metrics'
            }
            formatted_output = ', '.join(
                f'{key}: {value}' for key, value in display_outputs.items()
            )
            content = (
                f'{self.delegate.agent.name} finishes task with {formatted_output}'
            )
        else:
            # delegate state is ERROR
            # emit AgentDelegateObservation with error content
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )
            content = (
                f'{self.delegate.agent.name} encountered an error during execution.'
            )

        content = f'Delegated agent finished with result:\n\n{content}'

        # emit the delegate result observation
        obs = AgentDelegateObservation(outputs=delegate_outputs, content=content)

        # associate the delegate action with the initiating tool call
        for event in reversed(self.state.history):
            if isinstance(event, AgentDelegateAction):
                delegate_action = event
                obs.tool_call_metadata = delegate_action.tool_call_metadata
                break

        self.event_stream.add_event(obs, EventSource.AGENT)

        # unset delegate so parent can resume normal handling
        self.delegate = None