async def generate(self, messages: list[dict], _recursion_depth: int = 0) -> str:
        """Generate a response from the language model.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            _recursion_depth: Internal counter to prevent infinite recursion

        Returns:
            Generated text response

        Raises:
            ValueError: If messages are invalid or response is malformed
            RuntimeError: If max continuations exceeded or API call fails
        """
        # Validate inputs
        self._validate_messages(messages)

        # Check recursion depth
        if _recursion_depth >= self.MAX_CONTINUATIONS:
            msg = f"Maximum continuation depth ({self.MAX_CONTINUATIONS}) exceeded"
            raise RuntimeError(msg)

        # Convert messages to Langchain format
        converted_messages = [
            {
                "type": self._convert_role(msg.get("role", "system")),
                "data": {"content": self._extract_content(msg.get("content"))},
            }
            for msg in messages
        ]

        try:
            lc_messages = messages_from_dict(converted_messages)
        except Exception as exc:
            msg = f"Failed to convert messages to Langchain format: {exc}"
            raise ValueError(msg) from exc

        # Call the language model
        try:
            response = await self.langchain_model.agenerate(
                messages=[lc_messages],
            )
        except Exception as exc:
            msg = f"Language model API call failed: {exc}"
            raise RuntimeError(msg) from exc

        # Safely extract response
        if not response.generations or not response.generations[0]:
            msg = "Empty response from language model"
            raise ValueError(msg)

        choice0 = response.generations[0][0]

        if not hasattr(choice0, "message") or not hasattr(choice0.message, "content"):
            msg = "Malformed response from language model"
            raise ValueError(msg)

        chunk = self._extract_content(choice0.text)

        # Check if we need to continue due to max tokens
        generation_info = getattr(choice0, "generation_info", None)
        if generation_info and isinstance(generation_info, dict):
            finish_reason = generation_info.get("finish_reason")

            if finish_reason == "length":  # max tokens reached
                resp_msg = {
                    "role": "assistant",
                    "content": chunk,
                }
                continue_msg = {
                    "role": "user",
                    "content": (
                        "Continue the previous answer starting exactly from the last incomplete sentence. "
                        "Do not repeat anything. Do not add any prefix."
                    ),
                }
                next_messages = [
                    *messages,
                    resp_msg,
                    continue_msg,
                ]

                # Recursive call with depth tracking
                continuation = await self.generate(next_messages, _recursion_depth + 1)
                return chunk + continuation

        return chunk