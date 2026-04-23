def load_marian_model(self) -> MarianMTModel:
        state_dict, cfg = self.state_dict, self.hf_config

        if not cfg.static_position_embeddings:
            raise ValueError("config.static_position_embeddings should be True")
        model = MarianMTModel(cfg)

        if "hidden_size" in cfg.to_dict():
            raise ValueError("hidden_size is in config")
        load_layers_(
            model.model.encoder.layers,
            state_dict,
            BART_CONVERTER,
        )
        load_layers_(model.model.decoder.layers, state_dict, BART_CONVERTER, is_decoder=True)

        # handle tensors not associated with layers
        if self.cfg["tied-embeddings-src"]:
            wemb_tensor = nn.Parameter(torch.FloatTensor(self.wemb))
            bias_tensor = nn.Parameter(torch.FloatTensor(self.final_bias))
            model.model.shared.weight = wemb_tensor
            model.model.encoder.embed_tokens = model.model.decoder.embed_tokens = model.model.shared
        else:
            wemb_tensor = nn.Parameter(torch.FloatTensor(self.wemb))
            model.model.encoder.embed_tokens.weight = wemb_tensor

            decoder_wemb_tensor = nn.Parameter(torch.FloatTensor(self.dec_wemb))
            bias_tensor = nn.Parameter(torch.FloatTensor(self.final_bias))
            model.model.decoder.embed_tokens.weight = decoder_wemb_tensor

        # handle tied embeddings, otherwise "from_pretrained" loads them incorrectly
        if self.cfg["tied-embeddings"]:
            model.lm_head.weight.data = model.model.decoder.embed_tokens.weight.data.clone()

        model.final_logits_bias = bias_tensor

        if "Wpos" in state_dict:
            print("Unexpected: got Wpos")
            wpos_tensor = torch.tensor(state_dict["Wpos"])
            model.model.encoder.embed_positions.weight = wpos_tensor
            model.model.decoder.embed_positions.weight = wpos_tensor

        if cfg.normalize_embedding:
            if "encoder_emb_ln_scale_pre" not in state_dict:
                raise ValueError("encoder_emb_ln_scale_pre is not in state dictionary")
            raise NotImplementedError("Need to convert layernorm_embedding")

        if self.extra_keys:
            raise ValueError(f"Failed to convert {self.extra_keys}")

        if model.get_input_embeddings().padding_idx != self.pad_token_id:
            raise ValueError(
                f"Padding tokens {model.get_input_embeddings().padding_idx} and {self.pad_token_id} mismatched"
            )
        return model