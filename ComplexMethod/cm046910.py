def smart_chunk_text(self, text, chunk_size, stride, return_tokenized = True):
        """
        Intelligent chunking that:
        1. Respects sentence/paragraph boundaries
        2. Handles various text formats (.txt, .md, .json, etc.)
        3. Maintains context with stride overlap
        4. Returns tokenized chunks directly (more efficient) or text chunks
        """
        # First pass: tokenize the entire text to get accurate token counts
        tokenized = self.tokenizer(text, return_tensors = "pt", add_special_tokens = False)
        tokens = tokenized["input_ids"]

        # Handle different tokenizer return formats
        if hasattr(tokens, "__len__") and len(tokens) > 0:
            # If it's a nested structure, get the first element
            if hasattr(tokens[0], "__len__"):
                tokens = tokens[0]
        elif isinstance(tokens, int):
            # If tokenizer returns just a count, create a simple range
            tokens = list(range(tokens))

        if len(tokens) <= chunk_size:
            # Text is small enough to fit in one chunk
            if return_tokenized:
                # Add EOS token to the tokens if available
                eos_token_id = getattr(self.tokenizer, "eos_token_id", None)
                if eos_token_id is not None:
                    tokens = (
                        tokens.tolist() if hasattr(tokens, "tolist") else list(tokens)
                    )
                    tokens.append(eos_token_id)

                # Create attention mask
                attention_mask = [1] * len(tokens)
                return [{"input_ids": tokens, "attention_mask": attention_mask}]
            else:
                eos_token = self.tokenizer.eos_token if self.tokenizer.eos_token else ""
                return [text + eos_token]

        chunks = []
        start_idx = 0

        while start_idx < len(tokens):
            # Calculate end index for this chunk
            end_idx = min(start_idx + chunk_size, len(tokens))

            # Extract tokens for this chunk
            chunk_tokens = tokens[start_idx:end_idx]

            if return_tokenized:
                # Convert to list if it's a tensor
                chunk_tokens_list = (
                    chunk_tokens.tolist()
                    if hasattr(chunk_tokens, "tolist")
                    else list(chunk_tokens)
                )

                # Add EOS token if it's the last chunk or chunk is complete
                if end_idx == len(tokens) or len(chunk_tokens_list) == chunk_size:
                    eos_token_id = getattr(self.tokenizer, "eos_token_id", None)
                    if eos_token_id is not None:
                        chunk_tokens_list.append(eos_token_id)

                # Create attention mask (all tokens are attended to)
                attention_mask = [1] * len(chunk_tokens_list)

                chunks.append(
                    {"input_ids": chunk_tokens_list, "attention_mask": attention_mask}
                )
            else:
                # Decode back to text (backward compatibility)
                chunk_text = self.tokenizer.decode(
                    chunk_tokens, skip_special_tokens = True
                )

                # Add EOS token if it's the last chunk or chunk is complete
                if end_idx == len(tokens) or len(chunk_tokens) == chunk_size:
                    eos_token = (
                        self.tokenizer.eos_token if self.tokenizer.eos_token else ""
                    )
                    chunk_text += eos_token

                chunks.append(chunk_text)

            # Move to next chunk with stride overlap
            if end_idx == len(tokens):
                break
            start_idx += chunk_size - stride

        return chunks