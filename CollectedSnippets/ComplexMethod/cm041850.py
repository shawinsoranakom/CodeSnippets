def chunk_responses(responses, tokens, llm):
    try:
        encoding = tiktoken.encoding_for_model(llm.model)
        chunked_responses = []
        current_chunk = ""
        current_tokens = 0

        for response in responses:
            tokenized_response = encoding.encode(response)
            new_tokens = current_tokens + len(tokenized_response)

            # If the new token count exceeds the limit, handle the current chunk
            if new_tokens > tokens:
                # If current chunk is empty or response alone exceeds limit, add response as standalone
                if current_tokens == 0 or len(tokenized_response) > tokens:
                    chunked_responses.append(response)
                else:
                    chunked_responses.append(current_chunk)
                    current_chunk = response
                    current_tokens = len(tokenized_response)
                continue

            # Add response to the current chunk
            current_chunk += "\n\n" + response if current_chunk else response
            current_tokens = new_tokens

        # Add remaining chunk if not empty
        if current_chunk:
            chunked_responses.append(current_chunk)
    except Exception:
        chunked_responses = []
        current_chunk = ""
        current_chars = 0

        for response in responses:
            new_chars = current_chars + len(response)

            # If the new char count exceeds the limit, handle the current chunk
            if new_chars > tokens * 4:
                # If current chunk is empty or response alone exceeds limit, add response as standalone
                if current_chars == 0 or len(response) > tokens * 4:
                    chunked_responses.append(response)
                else:
                    chunked_responses.append(current_chunk)
                    current_chunk = response
                    current_chars = len(response)
                continue

            # Add response to the current chunk
            current_chunk += "\n\n" + response if current_chunk else response
            current_chars = new_chars

        # Add remaining chunk if not empty
        if current_chunk:
            chunked_responses.append(current_chunk)
    return chunked_responses