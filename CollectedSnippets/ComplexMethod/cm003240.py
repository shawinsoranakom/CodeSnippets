def _stack_split_outputs(self, seek_outputs, model_output_type, device, kwargs):
        # Stack back seek_outputs tensors after splitting them with the split_by_batch_index method
        outputs = {}
        for key in seek_outputs[0]:
            if key in ["sequences", "beam_indices", "token_timestamps"]:
                outputs[key] = torch.stack([v[key] for v in seek_outputs], dim=0).to(device)
            elif key in ["scores", "encoder_attentions", "encoder_hidden_states", "logits"]:
                outputs[key] = tuple(
                    torch.stack([v[key][i] for v in seek_outputs]).to(device) for i in range(len(seek_outputs[0][key]))
                )
            elif key == "sequences_scores":
                outputs[key] = torch.stack([v[key] for v in seek_outputs], dim=0).to(device)
            elif key in ["decoder_attentions", "decoder_hidden_states", "cross_attentions"]:
                outputs[key] = tuple(
                    tuple(
                        torch.stack([v[key][i][j] for v in seek_outputs]).squeeze(1).to(device)
                        for j in range(len(seek_outputs[0][key][0]))
                    )
                    for i in range(len(seek_outputs[0][key]))
                )
            elif key == "past_key_values":
                if seek_outputs[0][key] is not None:
                    all_past_key_values = []
                    for layer_idx in range(len(seek_outputs[0][key])):
                        self_attention_k, self_attention_v, cross_attention_k, cross_attention_v = (
                            torch.stack(
                                [
                                    getattr(getattr(sub_output[key], sub_cache).layers[layer_idx], sub_key)
                                    for sub_output in seek_outputs
                                ]
                            )
                            .squeeze(1)
                            .to(device)
                            for sub_cache in ["self_attention_cache", "cross_attention_cache"]
                            for sub_key in ["keys", "values"]
                        )
                        all_past_key_values.append(
                            (self_attention_k, self_attention_v, cross_attention_k, cross_attention_v)
                        )
                    outputs[key] = EncoderDecoderCache(tuple(all_past_key_values))
                else:
                    outputs[key] = None

        token_timestamps = outputs.get("token_timestamps")
        if token_timestamps is not None:
            model_output_type = dict

        return model_output_type(**outputs)