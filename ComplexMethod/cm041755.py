def __post_init__(self):
        if self.model_name_or_path is None:
            raise ValueError("Please provide `model_name_or_path`.")

        if self.adapter_name_or_path is not None:  # support merging multiple lora weights
            self.adapter_name_or_path = [path.strip() for path in self.adapter_name_or_path.split(",")]

        if self.add_tokens is not None:  # support multiple tokens
            self.add_tokens = [token.strip() for token in self.add_tokens.split(",")]

        # Process special tokens with priority: new_special_tokens_config > add_special_tokens
        if self.new_special_tokens_config is not None:
            # Priority 1: Load from YAML config (extracts both tokens and descriptions)
            try:
                cfg = OmegaConf.load(self.new_special_tokens_config)
                token_descriptions = OmegaConf.to_container(cfg)

                if not isinstance(token_descriptions, dict):
                    raise ValueError(
                        f"YAML config must be a dictionary mapping tokens to descriptions. "
                        f"Got: {type(token_descriptions)}"
                    )

                # Extract token list from config keys
                extracted_tokens = list(token_descriptions.keys())

                # Warn if both are set
                if self.add_special_tokens is not None:
                    logger.warning_rank0(
                        "Both 'new_special_tokens_config' and 'add_special_tokens' are set. "
                        f"Using tokens from config: {extracted_tokens}"
                    )

                # Override add_special_tokens with extracted tokens (as list)
                self.add_special_tokens = extracted_tokens

                # Store descriptions internally for later use (internal attribute)
                self._special_token_descriptions = token_descriptions

                logger.info_rank0(
                    f"Loaded {len(extracted_tokens)} special tokens with descriptions from: "
                    f"{self.new_special_tokens_config}"
                )

            except Exception as e:
                logger.error_rank0(
                    f"Failed to load special tokens config from '{self.new_special_tokens_config}': {e}"
                )
                raise

        elif self.add_special_tokens is not None:
            # Priority 2: Use simple comma-separated string (no descriptions)
            self.add_special_tokens = [token.strip() for token in self.add_special_tokens.split(",")]
            self._special_token_descriptions = None

        else:
            # No special tokens to add
            self._special_token_descriptions = None

        # Validate init method
        if self.init_special_tokens in ["desc_init", "desc_init_w_noise"]:
            if self._special_token_descriptions is None:
                logger.warning_rank0(
                    f"init_special_tokens='{self.init_special_tokens}' requires new_special_tokens_config. "
                    "Falling back to 'noise_init'"
                )
                self.init_special_tokens = "noise_init"