def forward(self, x, attention_mask=None, embeds=None, num_tokens=None, intermediate_output=None, final_layer_norm_intermediate=True, dtype=None, position_ids=None, embeds_info=[], past_key_values=None):
        if embeds is not None:
            x = embeds
        else:
            x = self.embed_tokens(x, out_dtype=dtype)

        if self.normalize_in:
            x *= self.config.hidden_size ** 0.5

        seq_len = x.shape[1]
        past_len = 0
        if past_key_values is not None and len(past_key_values) > 0:
            past_len = self.get_past_len(past_key_values)

        if position_ids is None:
            position_ids = torch.arange(past_len, past_len + seq_len, device=x.device).unsqueeze(0)

        freqs_cis = self.compute_freqs_cis(position_ids, x.device)

        mask = None
        if attention_mask is not None:
            mask = 1.0 - attention_mask.to(x.dtype).reshape((attention_mask.shape[0], 1, -1, attention_mask.shape[-1])).expand(attention_mask.shape[0], 1, seq_len, attention_mask.shape[-1])
            mask = mask.masked_fill(mask.to(torch.bool), torch.finfo(x.dtype).min / 4)

        if seq_len > 1:
            causal_mask = torch.empty(past_len + seq_len, past_len + seq_len, dtype=x.dtype, device=x.device).fill_(torch.finfo(x.dtype).min / 4).triu_(1)
            if mask is not None:
                mask += causal_mask
            else:
                mask = causal_mask

        optimized_attention = optimized_attention_for_device(x.device, mask=mask is not None, small_input=True)

        intermediate = None
        all_intermediate = None
        only_layers = None
        if intermediate_output is not None:
            if isinstance(intermediate_output, list):
                all_intermediate = []
                only_layers = set(intermediate_output)
            elif intermediate_output == "all":
                all_intermediate = []
                intermediate_output = None
            elif intermediate_output < 0:
                intermediate_output = len(self.layers) + intermediate_output

        next_key_values = []
        for i, layer in enumerate(self.layers):
            if all_intermediate is not None:
                if only_layers is None or (i in only_layers):
                    all_intermediate.append(x.unsqueeze(1).clone())

            past_kv = None
            if past_key_values is not None:
                past_kv = past_key_values[i] if len(past_key_values) > 0 else []

            x, current_kv = layer(
                x=x,
                attention_mask=mask,
                freqs_cis=freqs_cis,
                optimized_attention=optimized_attention,
                past_key_value=past_kv,
            )

            if current_kv is not None:
                next_key_values.append(current_kv)

            if i == intermediate_output:
                intermediate = x.clone()

        if self.norm is not None:
            x = self.norm(x)

        if all_intermediate is not None:
            if only_layers is None or ((i + 1) in only_layers):
                all_intermediate.append(x.unsqueeze(1).clone())

        if all_intermediate is not None:
            intermediate = torch.cat(all_intermediate, dim=1)

        if intermediate is not None and final_layer_norm_intermediate and self.norm is not None:
            intermediate = self.norm(intermediate)

        if len(next_key_values) > 0:
            return x, intermediate, next_key_values
        else:
            return x, intermediate