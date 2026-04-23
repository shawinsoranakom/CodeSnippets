def _format_mistral_template(self, messages: list, special_tokens: dict) -> str:
        """Format messages using Mistral template"""
        bos_token = special_tokens.get("bos_token", "<s>")
        formatted = bos_token

        system_msg = None
        conversation = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                conversation.append(msg)

        i = 0
        while i < len(conversation):
            if conversation[i]["role"] == "user":
                user_content = conversation[i]["content"]

                if system_msg and i == 0:
                    user_content = f"{system_msg}\n\n{user_content}"

                formatted += f"[INST] {user_content} [/INST]"

                if (
                    i + 1 < len(conversation)
                    and conversation[i + 1]["role"] == "assistant"
                ):
                    formatted += f" {conversation[i + 1]['content']}</s>"
                    i += 2
                else:
                    formatted += " "
                    break
            else:
                i += 1

        return formatted