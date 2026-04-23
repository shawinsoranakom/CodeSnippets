def _format_messages(self, prompt: str) -> list[dict[str, str]]:
        """Convert prompt to Messages API format."""
        messages = []

        # Handle legacy prompts that might have HUMAN_PROMPT/AI_PROMPT markers
        if self.HUMAN_PROMPT and self.HUMAN_PROMPT in prompt:
            # Split on human/assistant turns
            parts = prompt.split(self.HUMAN_PROMPT)

            for _, part in enumerate(parts):
                if not part.strip():
                    continue

                if self.AI_PROMPT and self.AI_PROMPT in part:
                    # Split human and assistant parts
                    human_part, assistant_part = part.split(self.AI_PROMPT, 1)
                    if human_part.strip():
                        messages.append({"role": "user", "content": human_part.strip()})
                    if assistant_part.strip():
                        messages.append(
                            {"role": "assistant", "content": assistant_part.strip()}
                        )
                # Just human content
                elif part.strip():
                    messages.append({"role": "user", "content": part.strip()})
        else:
            # Handle modern format or plain text
            # Clean prompt for Messages API
            content = re.sub(r"^\n*Human:\s*", "", prompt)
            content = re.sub(r"\n*Assistant:\s*.*$", "", content)
            if content.strip():
                messages.append({"role": "user", "content": content.strip()})

        # Ensure we have at least one message
        if not messages:
            messages = [{"role": "user", "content": prompt.strip() or "Hello"}]

        return messages