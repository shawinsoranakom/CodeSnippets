def __init__(self, source_dir, eos_token_id=0):
        npz_path = find_model_file(source_dir)
        self.state_dict = np.load(npz_path)
        cfg = load_config_from_state_dict(self.state_dict)
        if cfg["dim-vocabs"][0] != cfg["dim-vocabs"][1]:
            raise ValueError
        if "Wpos" in self.state_dict:
            raise ValueError("Wpos key in state dictionary")
        self.state_dict = dict(self.state_dict)
        if cfg["tied-embeddings-all"]:
            cfg["tied-embeddings-src"] = True
            cfg["tied-embeddings"] = True
        self.share_encoder_decoder_embeddings = cfg["tied-embeddings-src"]

        # create the tokenizer here because we need to know the eos_token_id
        self.source_dir = source_dir
        self.tokenizer = self.load_tokenizer()
        # retrieve EOS token and set correctly
        tokenizer_has_eos_token_id = (
            hasattr(self.tokenizer, "eos_token_id") and self.tokenizer.eos_token_id is not None
        )
        eos_token_id = self.tokenizer.eos_token_id if tokenizer_has_eos_token_id else 0

        if cfg["tied-embeddings-src"]:
            self.wemb, self.final_bias = add_emb_entries(self.state_dict["Wemb"], self.state_dict[BIAS_KEY], 1)
            self.pad_token_id = self.wemb.shape[0] - 1
            cfg["vocab_size"] = self.pad_token_id + 1
        else:
            self.wemb, _ = add_emb_entries(self.state_dict["encoder_Wemb"], self.state_dict[BIAS_KEY], 1)
            self.dec_wemb, self.final_bias = add_emb_entries(
                self.state_dict["decoder_Wemb"], self.state_dict[BIAS_KEY], 1
            )
            # still assuming that vocab size is same for encoder and decoder
            self.pad_token_id = self.wemb.shape[0] - 1
            cfg["vocab_size"] = self.pad_token_id + 1
            cfg["decoder_vocab_size"] = self.pad_token_id + 1

        if cfg["vocab_size"] != self.tokenizer.vocab_size:
            raise ValueError(
                f"Original vocab size {cfg['vocab_size']} and new vocab size {len(self.tokenizer.encoder)} mismatched."
            )

        # self.state_dict['Wemb'].sha
        self.state_keys = list(self.state_dict.keys())
        if "Wtype" in self.state_dict:
            raise ValueError("Wtype key in state dictionary")
        self._check_layer_entries()
        self.cfg = cfg
        hidden_size, intermediate_shape = self.state_dict["encoder_l1_ffn_W1"].shape
        if hidden_size != cfg["dim-emb"]:
            raise ValueError(f"Hidden size {hidden_size} and configured size {cfg['dim_emb']} mismatched")

        # Process decoder.yml
        decoder_yml = cast_marian_config(load_yaml(source_dir / "decoder.yml"))
        check_marian_cfg_assumptions(cfg)
        self.hf_config = MarianConfig(
            vocab_size=cfg["vocab_size"],
            decoder_vocab_size=cfg.get("decoder_vocab_size", cfg["vocab_size"]),
            share_encoder_decoder_embeddings=cfg["tied-embeddings-src"],
            decoder_layers=cfg["dec-depth"],
            encoder_layers=cfg["enc-depth"],
            decoder_attention_heads=cfg["transformer-heads"],
            encoder_attention_heads=cfg["transformer-heads"],
            decoder_ffn_dim=cfg["transformer-dim-ffn"],
            encoder_ffn_dim=cfg["transformer-dim-ffn"],
            d_model=cfg["dim-emb"],
            activation_function=cfg["transformer-ffn-activation"],
            pad_token_id=self.pad_token_id,
            eos_token_id=eos_token_id,
            forced_eos_token_id=eos_token_id,
            bos_token_id=0,
            max_position_embeddings=cfg["dim-emb"],
            scale_embedding=True,
            normalize_embedding="n" in cfg["transformer-preprocess"],
            static_position_embeddings=not cfg["transformer-train-position-embeddings"],
            tie_word_embeddings=cfg["tied-embeddings"],
            dropout=0.1,  # see opus-mt-train repo/transformer-dropout param.
            # default: add_final_layer_norm=False,
            num_beams=decoder_yml["beam-size"],
            decoder_start_token_id=self.pad_token_id,
            bad_words_ids=[[self.pad_token_id]],
            max_length=512,
        )