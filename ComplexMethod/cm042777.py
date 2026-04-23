def _messages_to_prompt(self, messages: Sequence[ChatMessage]) -> str:
        prompt = ""
        has_system_message = False

        for i, message in enumerate(messages):
            if not message or message.content is None:
                continue
            if message.role == MessageRole.SYSTEM:
                prompt += f"{self.B_SYS}\n\n{message.content.strip()}{self.E_SYS}"
                has_system_message = True
            else:
                role_header = f"{self.B_INST}{message.role.value}{self.E_INST}"
                prompt += f"{role_header}\n\n{message.content.strip()}{self.EOT}"

            # Add assistant header if the last message is not from the assistant
            if i == len(messages) - 1 and message.role != MessageRole.ASSISTANT:
                prompt += f"{self.ASSISTANT_INST}\n\n"

        # Add default system prompt if no system message was provided
        if not has_system_message:
            prompt = (
                f"{self.B_SYS}\n\n{self.DEFAULT_SYSTEM_PROMPT}{self.E_SYS}" + prompt
            )

        # TODO: Implement tool handling logic

        return prompt