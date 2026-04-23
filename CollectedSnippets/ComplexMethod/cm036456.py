def merge_pooling_params(
        self,
        params: PoolingParams | None = None,
    ) -> PoolingParams:
        if params is None:
            params = PoolingParams()
        # refer to PoolingCompletionRequest.to_pooling_params
        # set and verify pooling params
        params.skip_reading_prefix_cache = True

        raw_embed_request = self.embed_request_queue.pop(0)
        if raw_embed_request.embed_task not in EMBED_TASKS:
            raise ValueError(
                f"Unsupported task {raw_embed_request}, "
                f"Supported tasks are {EMBED_TASKS}"
            )
        params.task = "embed&token_classify"
        params.use_activation = raw_embed_request.use_activation
        if params.use_activation is None:
            params.use_activation = True

        params.dimensions = raw_embed_request.dimensions

        model_config: ModelConfig = self.vllm_config.model_config
        for param in self.default_pooling_params:
            if getattr(params, param, None) is None:
                setattr(params, param, self.default_pooling_params[param])

        if params.dimensions is not None:
            if not model_config.is_matryoshka:
                raise ValueError(
                    f'Model "{model_config.served_model_name}" does not '
                    f"support matryoshka representation, "
                    f"changing output dimensions will lead to poor results."
                )

            mds = model_config.matryoshka_dimensions
            if mds is not None:
                if params.dimensions not in mds:
                    raise ValueError(
                        f"Model {model_config.served_model_name!r} "
                        f"only supports {str(mds)} matryoshka dimensions, "
                        f"use other output dimensions will "
                        f"lead to poor results."
                    )
            elif params.dimensions < 1:
                raise ValueError("Dimensions must be greater than 0")
        return params