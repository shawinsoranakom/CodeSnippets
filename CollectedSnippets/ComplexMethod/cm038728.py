def is_prefix_caching_supported(self) -> bool:
        attn_type = self.attn_type

        if pooler_config := self.pooler_config:
            # for pooling models
            if attn_type == "encoder_only":
                logger.debug(
                    "Pooling models with bidirectional attn "
                    "do not support prefix caching."
                )
                return False

            if attn_type == "decoder":
                if (
                    pooler_config.seq_pooling_type in ("MEAN", "CLS")
                    or pooler_config.tok_pooling_type == "STEP"
                ):
                    logger.debug(
                        "Pooling models with causal attn and %s/%s pooling "
                        "do not support prefix caching.",
                        pooler_config.seq_pooling_type,
                        pooler_config.tok_pooling_type,
                    )
                    return False
                else:
                    logger.debug(
                        "Pooling models with causal attn and %s/%s pooling "
                        "support prefix caching.",
                        pooler_config.seq_pooling_type,
                        pooler_config.tok_pooling_type,
                    )
                    return True

            # vllm currently does not have pooling models using hybrid,
            # attention_free or encoder_decoder attn types.
            return False
        else:
            # for generative models
            if attn_type == "hybrid":
                logger.debug(
                    "Hybrid models do not support prefix caching since the feature "
                    "is still experimental."
                )
                return False
            elif attn_type == "attention_free":
                logger.debug(
                    "Attention free models do not support prefix caching since the "
                    "feature is still experimental."
                )
                return False
            elif attn_type == "encoder_decoder":
                logger.debug("Encoder decoder models do not support prefix caching.")
                return False
            else:  # attn_type == "decoder"
                logger.debug("Generative models support prefix caching.")
                return True