async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        chunk = []
        cur_tokens, max_tokens = 0, input_data.max_tokens
        cur_size, max_size = 0, input_data.max_size

        for value in input_data.values:
            if max_tokens:
                tokens = estimate_token_count_str(value)
            else:
                tokens = 0

            # Check if adding this value would exceed either limit
            if (max_tokens and (cur_tokens + tokens > max_tokens)) or (
                max_size and (cur_size + 1 > max_size)
            ):
                yield "list", chunk
                chunk = [value]
                cur_size, cur_tokens = 1, tokens
            else:
                chunk.append(value)
                cur_size, cur_tokens = cur_size + 1, cur_tokens + tokens

        # Yield final chunk if any
        if chunk or not input_data.values:
            yield "list", chunk