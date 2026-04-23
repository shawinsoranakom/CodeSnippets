def _get_resized_lm_head(
        self,
        old_lm_head: nn.Linear,
        new_num_tokens: int | None = None,
        transposed: bool = False,
        mean_resizing: bool = True,
    ) -> nn.Linear:
        """
        Build a resized Linear Module from a provided old Linear Module. Increasing the size will add newly initialized
        vectors at the end. Reducing the size will remove vectors from the end

        Args:
            old_lm_head (`torch.nn.Linear`):
                Old lm head liner layer to be resized.
            new_num_tokens (`int`, *optional*):
                New number of tokens in the linear matrix.

                Increasing the size will add newly initialized vectors at the end. Reducing the size will remove
                vectors from the end. If not provided or `None`, just returns a pointer to the input tokens
                `torch.nn.Linear` module of the model without doing anything. transposed (`bool`, *optional*, defaults
                to `False`): Whether `old_lm_head` is transposed or not. If True `old_lm_head.size()` is `lm_head_dim,
                vocab_size` else `vocab_size, lm_head_dim`.
            mean_resizing (`bool`):
                Whether to initialize the added embeddings from a multivariate normal distribution that has old embeddings' mean and
                covariance or to initialize them with a normal distribution that has a mean of zero and std equals `config.initializer_range`.

                Setting `mean_resizing` to `True` is useful when increasing the size of the embeddings of causal language models,
                where the generated tokens' probabilities will not be affected by the added embeddings because initializing the new embeddings with the
                old embeddings' mean will reduce the kl-divergence between the next token probability before and after adding the new embeddings.
                Refer to this article for more information: https://nlp.stanford.edu/~johnhew/vocab-expansion.html

        Return:
            `torch.nn.Linear`: Pointer to the resized Linear Module or the old Linear Module if `new_num_tokens` is
            `None`
        """

        if new_num_tokens is None:
            return old_lm_head

        is_quantized = hasattr(self, "hf_quantizer") and self.hf_quantizer is not None
        if is_deepspeed_zero3_enabled() and not is_quantized:
            import deepspeed

            with deepspeed.zero.GatheredParameters(old_lm_head.weight, modifier_rank=None):
                old_num_tokens, old_lm_head_dim = (
                    old_lm_head.weight.size() if not transposed else old_lm_head.weight.t().size()
                )
        else:
            old_num_tokens, old_lm_head_dim = (
                old_lm_head.weight.size() if not transposed else old_lm_head.weight.t().size()
            )

        if old_num_tokens == new_num_tokens and not is_deepspeed_zero3_enabled():
            old_lm_head.out_features = new_num_tokens  # maybe weights are tied which doesn't update attr
            return old_lm_head

        if not isinstance(old_lm_head, nn.Linear):
            raise TypeError(
                f"Old language model head is of type {type(old_lm_head)}, which is not an instance of {nn.Linear}. You"
                " should either use a different resize function or make sure that `old_lm_head` are an instance of"
                f" {nn.Linear}."
            )

        # Build new lm head
        new_lm_head_shape = (old_lm_head_dim, new_num_tokens) if not transposed else (new_num_tokens, old_lm_head_dim)
        has_new_lm_head_bias = old_lm_head.bias is not None

        # When using DeepSpeed ZeRO-3, we shouldn't create new embeddings with DeepSpeed init
        # because the shape of the new embedding layer is used across various modeling files
        # as well as to update config vocab size. Shape will be 0 when using DeepSpeed init leading
        # to errors when training.
        new_lm_head = nn.Linear(
            *new_lm_head_shape,
            bias=has_new_lm_head_bias,
            device=old_lm_head.weight.device,
            dtype=old_lm_head.weight.dtype,
        )

        if new_num_tokens > old_num_tokens and not mean_resizing:
            # initialize new embeddings (in particular added tokens) with a mean of 0 and std equals `config.initializer_range`.
            self._init_weights(new_lm_head)

        elif new_num_tokens > old_num_tokens and mean_resizing:
            # initialize new lm_head weights (in particular added tokens). The new lm_head weights
            # will be initialized from a multivariate normal distribution that has old embeddings' mean and covariance.
            # as described in this article: https://nlp.stanford.edu/~johnhew/vocab-expansion.html
            logger.warning_once(
                "The new lm_head weights will be initialized from a multivariate normal distribution that has old embeddings' mean and covariance. "
                "As described in this article: https://nlp.stanford.edu/~johnhew/vocab-expansion.html. "
                "To disable this, use `mean_resizing=False`"
            )

            added_num_tokens = new_num_tokens - old_num_tokens
            if is_deepspeed_zero3_enabled() and not is_quantized:
                import deepspeed

                params = [old_lm_head.weight]
                if has_new_lm_head_bias:
                    params += [old_lm_head.bias]
                with deepspeed.zero.GatheredParameters(params, modifier_rank=None):
                    self._init_added_lm_head_weights_with_mean(
                        old_lm_head, new_lm_head, old_lm_head_dim, old_num_tokens, added_num_tokens, transposed
                    )
                    if has_new_lm_head_bias:
                        self._init_added_lm_head_bias_with_mean(old_lm_head, new_lm_head, added_num_tokens)

            else:
                self._init_added_lm_head_weights_with_mean(
                    old_lm_head, new_lm_head, old_lm_head_dim, old_num_tokens, added_num_tokens, transposed
                )
                if has_new_lm_head_bias:
                    self._init_added_lm_head_bias_with_mean(old_lm_head, new_lm_head, added_num_tokens)

        num_tokens_to_copy = min(old_num_tokens, new_num_tokens)

        if is_deepspeed_zero3_enabled() and not is_quantized:
            import deepspeed

            params = [old_lm_head.weight, old_lm_head.bias, new_lm_head.weight, new_lm_head.bias]
            with deepspeed.zero.GatheredParameters(params, modifier_rank=0):
                self._copy_lm_head_original_to_resized(
                    new_lm_head, old_lm_head, num_tokens_to_copy, transposed, has_new_lm_head_bias
                )
        else:
            self._copy_lm_head_original_to_resized(
                new_lm_head, old_lm_head, num_tokens_to_copy, transposed, has_new_lm_head_bias
            )

        new_lm_head._is_hf_initialized = True
        return new_lm_head