def _verify_pooling_task(self, pooling_task: PoolingTask | None):
        if self.runner_type != "pooling":
            raise ValueError(
                "LLM.encode() is only supported for pooling models. "
                "Try passing `--runner pooling` to use the model as a "
                "pooling model."
            )

        if pooling_task is None:
            raise ValueError(
                "pooling_task required for `LLM.encode`\n"
                "Please use one of the more specific methods or set the "
                "pooling_task when using `LLM.encode`:\n"
                "  - For embeddings, use `LLM.embed(...)` "
                'or `pooling_task="embed"`.\n'
                "  - For classification logits, use `LLM.classify(...)` "
                'or `pooling_task="classify"`.\n'
                "  - For similarity scores, use `LLM.score(...)`.\n"
                "  - For rewards, use `LLM.reward(...)` "
                'or `pooling_task="token_classify"`\n'
                "  - For token classification, "
                'use `pooling_task="token_classify"`\n'
                '  - For multi-vector retrieval, use `pooling_task="token_embed"`'
            )

        if (
            pooling_task in ("embed", "token_embed")
            and pooling_task not in self.supported_tasks
        ):
            raise ValueError(
                "Embedding API is not supported by this model. "
                "Try converting the model using `--convert embed`."
            )

        if (
            pooling_task in ("classify", "token_classify")
            and pooling_task not in self.supported_tasks
        ):
            raise ValueError(
                "Classification API is not supported by this model. "
                "Try converting the model using `--convert classify`."
            )

        # plugin task uses io_processor.parse_request to verify inputs
        if pooling_task != "plugin" and pooling_task != self.pooling_task:
            if pooling_task not in self.supported_tasks:
                raise ValueError(
                    f"Unsupported task: {pooling_task!r} "
                    f"Supported tasks: {self.supported_tasks}"
                )
            else:
                raise ValueError(
                    f"Try switching the model's pooling_task "
                    f'via `PoolerConfig(task="{pooling_task}")`'
                )

        if pooling_task == "plugin" and "plugin" not in self.pooling_io_processors:
            raise ValueError(
                "No IOProcessor plugin installed. Please refer "
                "to the documentation and to the "
                "'prithvi_geospatial_mae_io_processor' "
                "offline inference example for more details."
            )