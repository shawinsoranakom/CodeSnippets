def extract_reasoning(
        self, model_output: str, request: "ChatCompletionRequest | ResponsesRequest"
    ) -> tuple[str | None, str | None]:
        """
        Extract reasoning content from the model output.
        """
        if not model_output:
            return (None, "")

        # Check if the start token is present in the model output, remove it
        # if it is present.
        prev_bot_token, bot_token, post_bot_token = model_output.partition(
            self.start_token
        )

        has_bot_token = bool(bot_token)
        # Valid EOT tokens should follow BOT token
        has_valid_eot_token = has_bot_token and self.end_token in post_bot_token

        # 1. If there is BOT token followed by EOT token
        if has_bot_token and has_valid_eot_token:
            prev_eot_token, _, post_eot_token = post_bot_token.partition(self.end_token)
            # If model is well prompted and trained prev_bot_token should be ""
            content = prev_bot_token + post_eot_token
            return prev_eot_token, content if content else None
        # 2. Only BOT token
        elif has_bot_token:
            # If model is well prompted and trained prev_bot_token should be ""
            return post_bot_token, prev_bot_token if prev_bot_token else None
        # 3. EOT token has been outputted without BOT or neither has been outputted
        else:
            has_non_valid_eot_token = self.end_token in prev_bot_token
            # 3.a EOT token has been outputted without BOT
            # If model is well prompted and trained `has_non_valid_eot_token` should
            # be `False` and the parser outputs all tokens as 'content'
            if has_non_valid_eot_token:
                prev_eot_token, _, post_eot_token = prev_bot_token.partition(
                    self.end_token
                )
                return None, prev_eot_token + post_eot_token
            # 3.b neither BOT or EOT have been outputted
            else:
                return None, prev_bot_token