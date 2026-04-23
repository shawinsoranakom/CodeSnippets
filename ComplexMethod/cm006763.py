def build_status_message(self, message: AIMessage):
        """Builds a status message from an AIMessage object.

        Args:
            message (AIMessage): The AIMessage object to build the status message from.

        Returns:
            The status message.
        """
        if message.response_metadata:
            # Build a well formatted status message
            content = message.content
            response_metadata = message.response_metadata
            openai_keys = ["token_usage", "model_name", "finish_reason"]
            inner_openai_keys = ["completion_tokens", "prompt_tokens", "total_tokens"]
            anthropic_keys = ["model", "usage", "stop_reason"]
            inner_anthropic_keys = ["input_tokens", "output_tokens"]
            if all(key in response_metadata for key in openai_keys) and all(
                key in response_metadata["token_usage"] for key in inner_openai_keys
            ):
                token_usage = response_metadata["token_usage"]
                status_message = {
                    "tokens": {
                        "input": token_usage["prompt_tokens"],
                        "output": token_usage["completion_tokens"],
                        "total": token_usage["total_tokens"],
                        "stop_reason": response_metadata["finish_reason"],
                        "response": content,
                    }
                }

            elif all(key in response_metadata for key in anthropic_keys) and all(
                key in response_metadata["usage"] for key in inner_anthropic_keys
            ):
                usage = response_metadata["usage"]
                status_message = {
                    "tokens": {
                        "input": usage["input_tokens"],
                        "output": usage["output_tokens"],
                        "stop_reason": response_metadata["stop_reason"],
                        "response": content,
                    }
                }
            else:
                status_message = f"Response: {content}"  # type: ignore[assignment]
        else:
            status_message = f"Response: {message.content}"  # type: ignore[assignment]
        return status_message