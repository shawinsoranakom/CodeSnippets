def generate(
        exported_program: torch.export.ExportedProgram,
        tokenizer,
        prompt: str,
        max_new_tokens: int = 20,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 1.0,
        device: str = "cpu",
    ) -> str:
        """
        Generate a sequence of tokens using an exported program.

        Args:
            exported_program (`torch.export.ExportedProgram`): The exported model being used for generate.
            tokenizer: The tokenizer to use.
            prompt (str): The input prompt.
            max_new_tokens (int): Maximum number of new tokens to generate.
            do_sample (bool): Whether to use sampling or greedy decoding.
            temperature (float): The temperature for sampling.
            top_k (int): The number of highest probability tokens to keep for top-k sampling.
            top_p (float): The cumulative probability for nucleus sampling.
            device (str): The device to use.

        Returns:
            str: The generated text.
        """
        # Get the module from the exported program
        exported_module = exported_program.module()

        # Tokenize the prompt
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)

        # Initialize with the prompt
        generated_ids = input_ids.clone()

        # Process the prompt tokens first
        curr_position = 0
        for i in range(input_ids.shape[1]):
            # Process one token at a time
            curr_input_ids = input_ids[:, i : i + 1]
            curr_cache_position = torch.tensor([curr_position], dtype=torch.long, device=device)

            # Forward pass
            _ = exported_module(input_ids=curr_input_ids, cache_position=curr_cache_position)
            curr_position += 1

        # Generate new tokens
        for _ in range(max_new_tokens):
            # Get the last token as input
            curr_input_ids = generated_ids[:, -1:]
            curr_cache_position = torch.tensor([curr_position], dtype=torch.long, device=device)

            # Forward pass to get next token logits
            outputs = exported_module(input_ids=curr_input_ids, cache_position=curr_cache_position)

            # Get the next token ID
            if do_sample:
                # Apply temperature
                if temperature > 0:
                    logits = outputs / temperature
                else:
                    logits = outputs

                # Apply top-k filtering
                if top_k > 0:
                    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                    logits[indices_to_remove] = float("-inf")

                # Apply top-p (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

                    # Remove tokens with cumulative probability above the threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    # Shift the indices to the right to keep also the first token above the threshold
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0

                    # Scatter sorted tensors to original indexing
                    indices_to_remove = sorted_indices_to_remove.scatter(-1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = float("-inf")

                # Sample from the filtered distribution
                probs = torch.softmax(logits, dim=-1)
                next_token_id = torch.multinomial(probs, num_samples=1)
            else:
                # Greedy decoding
                next_token_id = outputs.argmax(dim=-1, keepdim=True)

            # Ensure next_token_id has the right shape before concatenation
            if next_token_id.dim() > 2:
                next_token_id = next_token_id.squeeze(-1)

            # Append to the generated sequence
            generated_ids = torch.cat([generated_ids, next_token_id], dim=-1)
            curr_position += 1

            # Stop if we generate an EOS token
            if next_token_id.item() == tokenizer.eos_token_id:
                break

        # Decode the generated text
        return tokenizer.decode(generated_ids[0], skip_special_tokens=True)