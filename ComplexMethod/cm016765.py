def sample_manual_loop_no_classes(
    model,
    ids=None,
    execution_dtype=None,
    cfg_scale: float = 2.0,
    temperature: float = 0.85,
    top_p: float = 0.9,
    top_k: int = None,
    min_p: float = 0.000,
    seed: int = 1,
    min_tokens: int = 1,
    max_new_tokens: int = 2048,
    audio_start_id: int = 151669,  # The cutoff ID for audio codes
    audio_end_id: int = 215669,
    eos_token_id: int = 151645,
):
    if ids is None:
        return []
    device = model.execution_device

    if execution_dtype is None:
        if comfy.model_management.should_use_bf16(device):
            execution_dtype = torch.bfloat16
        else:
            execution_dtype = torch.float32

    embeds, attention_mask, num_tokens, embeds_info = model.process_tokens(ids, device)
    embeds_batch = embeds.shape[0]

    output_audio_codes = []
    past_key_values = []
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    model_config = model.transformer.model.config
    past_kv_shape = [embeds_batch, model_config.num_key_value_heads, embeds.shape[1] + min_tokens, model_config.head_dim]

    for x in range(model_config.num_hidden_layers):
        past_key_values.append((torch.empty(past_kv_shape, device=device, dtype=execution_dtype), torch.empty(past_kv_shape, device=device, dtype=execution_dtype), 0))

    progress_bar = comfy.utils.ProgressBar(max_new_tokens)

    for step in comfy.utils.model_trange(max_new_tokens, desc="LM sampling"):
        outputs = model.transformer(None, attention_mask, embeds=embeds.to(execution_dtype), num_tokens=num_tokens, intermediate_output=None, dtype=execution_dtype, embeds_info=embeds_info, past_key_values=past_key_values)
        next_token_logits = model.transformer.logits(outputs[0])[:, -1]
        past_key_values = outputs[2]

        if cfg_scale != 1.0:
            cond_logits = next_token_logits[0:1]
            uncond_logits = next_token_logits[1:2]
            cfg_logits = uncond_logits + cfg_scale * (cond_logits - uncond_logits)
        else:
            cfg_logits = next_token_logits[0:1]

        use_eos_score = eos_token_id is not None and eos_token_id < audio_start_id and min_tokens < step
        if use_eos_score:
            eos_score = cfg_logits[:, eos_token_id].clone()

        remove_logit_value = torch.finfo(cfg_logits.dtype).min
        # Only generate audio tokens
        cfg_logits[:, :audio_start_id] = remove_logit_value
        cfg_logits[:, audio_end_id:] = remove_logit_value

        if use_eos_score:
            cfg_logits[:, eos_token_id] = eos_score

        if top_k is not None and top_k > 0:
            top_k_vals, _ = torch.topk(cfg_logits, top_k)
            min_val = top_k_vals[..., -1, None]
            cfg_logits[cfg_logits < min_val] = remove_logit_value

        if min_p is not None and min_p > 0:
            probs = torch.softmax(cfg_logits, dim=-1)
            p_max = probs.max(dim=-1, keepdim=True).values
            indices_to_remove = probs < (min_p * p_max)
            cfg_logits[indices_to_remove] = remove_logit_value

        if top_p is not None and top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(cfg_logits, descending=True)
            cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
            cfg_logits[indices_to_remove] = remove_logit_value

        if temperature > 0:
            cfg_logits = cfg_logits / temperature
            next_token = torch.multinomial(torch.softmax(cfg_logits, dim=-1), num_samples=1, generator=generator).squeeze(1)
        else:
            next_token = torch.argmax(cfg_logits, dim=-1)

        token = next_token.item()

        if token == eos_token_id:
            break

        embed, _, _, _ = model.process_tokens([[token]], device)
        embeds = embed.repeat(embeds_batch, 1, 1)
        attention_mask = torch.cat([attention_mask, torch.ones((embeds_batch, 1), device=device, dtype=attention_mask.dtype)], dim=1)

        output_audio_codes.append(token - audio_start_id)
        progress_bar.update_absolute(step)

    return output_audio_codes