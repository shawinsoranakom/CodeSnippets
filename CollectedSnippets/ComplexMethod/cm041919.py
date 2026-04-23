def compress_messages(
        self,
        messages: list[dict],
        compress_type: CompressType = CompressType.NO_COMPRESS,
        max_token: int = 128000,
        threshold: float = 0.8,
    ) -> list[dict]:
        """Compress messages to fit within the token limit.
        Args:
            messages (list[dict]): List of messages to compress.
            compress_type (CompressType, optional): Compression strategy. Defaults to CompressType.NO_COMPRESS.
            max_token (int, optional): Maximum token limit. Defaults to 128000. Not effective if token limit can be found in TOKEN_MAX.
            threshold (float): Token limit threshold. Defaults to 0.8. Reserve 20% of the token limit for completion message.
        """
        if compress_type == CompressType.NO_COMPRESS:
            return messages

        max_token = TOKEN_MAX.get(self.model, max_token)
        keep_token = int(max_token * threshold)
        compressed = []

        # Always keep system messages
        # NOTE: Assume they do not exceed token limit
        system_msg_val = self._system_msg("")["role"]
        system_msgs = []
        for i, msg in enumerate(messages):
            if msg["role"] == system_msg_val:
                system_msgs.append(msg)
            else:
                user_assistant_msgs = messages[i:]
                break
        # system_msgs = [msg for msg in messages if msg["role"] == system_msg_val]
        # user_assistant_msgs = [msg for msg in messages if msg["role"] != system_msg_val]
        compressed.extend(system_msgs)
        current_token_count = self.count_tokens(system_msgs)

        if compress_type in [CompressType.POST_CUT_BY_TOKEN, CompressType.POST_CUT_BY_MSG]:
            # Under keep_token constraint, keep as many latest messages as possible
            for i, msg in enumerate(reversed(user_assistant_msgs)):
                token_count = self.count_tokens([msg])
                if current_token_count + token_count <= keep_token:
                    compressed.insert(len(system_msgs), msg)
                    current_token_count += token_count
                else:
                    if compress_type == CompressType.POST_CUT_BY_TOKEN or len(compressed) == len(system_msgs):
                        # Truncate the message to fit within the remaining token count; Otherwise, discard the msg. If compressed has no user or assistant message, enforce cutting by token
                        truncated_content = msg["content"][-(keep_token - current_token_count) :]
                        compressed.insert(len(system_msgs), {"role": msg["role"], "content": truncated_content})
                    logger.warning(
                        f"Truncated messages with {compress_type} to fit within the token limit. "
                        f"The first user or assistant message after truncation (originally the {i}-th message from last): {compressed[len(system_msgs)]}."
                    )
                    break

        elif compress_type in [CompressType.PRE_CUT_BY_TOKEN, CompressType.PRE_CUT_BY_MSG]:
            # Under keep_token constraint, keep as many earliest messages as possible
            for i, msg in enumerate(user_assistant_msgs):
                token_count = self.count_tokens([msg])
                if current_token_count + token_count <= keep_token:
                    compressed.append(msg)
                    current_token_count += token_count
                else:
                    if compress_type == CompressType.PRE_CUT_BY_TOKEN or len(compressed) == len(system_msgs):
                        # Truncate the message to fit within the remaining token count; Otherwise, discard the msg. If compressed has no user or assistant message, enforce cutting by token
                        truncated_content = msg["content"][: keep_token - current_token_count]
                        compressed.append({"role": msg["role"], "content": truncated_content})
                    logger.warning(
                        f"Truncated messages with {compress_type} to fit within the token limit. "
                        f"The last user or assistant message after truncation (originally the {i}-th message): {compressed[-1]}."
                    )
                    break

        return compressed