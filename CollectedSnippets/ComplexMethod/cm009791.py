def _replace_message_id(self, maybe_message: Any) -> Any:
        if isinstance(maybe_message, BaseMessage):
            maybe_message.id = str(next(self.uuids_generator))
        if isinstance(maybe_message, ChatGeneration):
            maybe_message.message.id = str(next(self.uuids_generator))
        if isinstance(maybe_message, LLMResult):
            for i, gen_list in enumerate(maybe_message.generations):
                for j, gen in enumerate(gen_list):
                    maybe_message.generations[i][j] = self._replace_message_id(gen)
        if isinstance(maybe_message, dict):
            for k, v in maybe_message.items():
                maybe_message[k] = self._replace_message_id(v)
        if isinstance(maybe_message, list):
            for i, v in enumerate(maybe_message):
                maybe_message[i] = self._replace_message_id(v)

        return maybe_message