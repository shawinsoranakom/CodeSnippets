def generate(self, embeds=None, do_sample=True, max_length=256, temperature=1.0, top_k=50, top_p=0.9, min_p=0.0, repetition_penalty=1.0, seed=42, stop_tokens=None, initial_tokens=[], execution_dtype=None, min_tokens=0, presence_penalty=0.0):
        device = embeds.device

        if stop_tokens is None:
            stop_tokens = self.model.config.stop_tokens

        if execution_dtype is None:
            if comfy.model_management.should_use_bf16(device):
                execution_dtype = torch.bfloat16
            else:
                execution_dtype = torch.float32
        embeds = embeds.to(execution_dtype)

        if embeds.ndim == 2:
            embeds = embeds.unsqueeze(0)

        max_cache_len = embeds.shape[1] + max_length
        past_key_values = self.init_kv_cache(embeds.shape[0], max_cache_len, device, execution_dtype)

        generator = torch.Generator(device=device).manual_seed(seed) if do_sample else None

        generated_token_ids = []
        pbar = comfy.utils.ProgressBar(max_length)

        # Generation loop
        for step in tqdm(range(max_length), desc="Generating tokens"):
            x, _, past_key_values = self.model.forward(None, embeds=embeds, attention_mask=None, past_key_values=past_key_values)
            logits = self.logits(x)[:, -1]
            next_token = self.sample_token(logits, temperature, top_k, top_p, min_p, repetition_penalty, initial_tokens + generated_token_ids, generator, do_sample=do_sample, presence_penalty=presence_penalty)
            token_id = next_token[0].item()
            generated_token_ids.append(token_id)

            embeds = self.model.embed_tokens(next_token).to(execution_dtype)
            pbar.update(1)

            if token_id in stop_tokens:
                break

        return generated_token_ids