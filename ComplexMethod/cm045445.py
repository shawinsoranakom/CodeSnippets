async def update_message_thread(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> None:
        await super().update_message_thread(messages)

        # Find the node that ran in the current turn.
        message = messages[-1]
        if message.source not in self._graph.nodes:
            # Ignore messages from sources outside of the graph.
            return
        assert isinstance(message, BaseChatMessage)
        source = message.source

        # Propagate the update to the children of the node.
        for edge in self._edges[source]:
            # Use the new check_condition method that handles both string and callable conditions
            if not edge.check_condition(message):
                continue

            target = edge.target
            activation_group = edge.activation_group

            if self._activation[target][activation_group] == "all":
                self._remaining[target][activation_group] -= 1
                if self._remaining[target][activation_group] == 0:
                    # If all parents are done, add to the ready queue.
                    self._ready.append(target)
                    # Track which activation group was triggered
                    self._save_triggered_activation_group(target, activation_group)
            else:
                # If activation is any, add to the ready queue if not already enqueued.
                if not self._enqueued_any[target][activation_group]:
                    self._ready.append(target)
                    self._enqueued_any[target][activation_group] = True
                    # Track which activation group was triggered
                    self._save_triggered_activation_group(target, activation_group)