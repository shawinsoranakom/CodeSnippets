def split_by_batch_index(values, key, batch_idx, is_shortform, beam_indices=None):
            if beam_indices is not None and key == "scores":
                return [v[beam_idx].cpu() for (v, beam_idx) in zip(values, beam_indices[batch_idx][: len(values)])]
            if key in ["scores", "encoder_attentions", "encoder_hidden_states", "logits"]:
                return [v[batch_idx].cpu() for v in values]
            if key in ["decoder_attentions", "decoder_hidden_states", "cross_attentions"]:
                return tuple(tuple(w[batch_idx][None].cpu() for w in v) for v in values)
            elif key == "past_key_values":
                if not is_shortform:
                    # we don't save `past_key_values` as this is too costly for longform
                    return None
                all_past_key_values = []
                for layer_idx in range(self.config.decoder_layers):
                    layer_cache = (
                        values.self_attention_cache.layers[layer_idx].keys[batch_idx][None].cpu(),
                        values.self_attention_cache.layers[layer_idx].values[batch_idx][None].cpu(),
                        values.cross_attention_cache.layers[layer_idx].keys[batch_idx][None].cpu(),
                        values.cross_attention_cache.layers[layer_idx].values[batch_idx][None].cpu(),
                    )
                    all_past_key_values.append(layer_cache)
                return EncoderDecoderCache(all_past_key_values)

            return values[batch_idx].cpu()