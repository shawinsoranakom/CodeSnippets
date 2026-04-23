def get_pooling_task(
        self, supported_tasks: tuple[SupportedTask, ...]
    ) -> PoolingTask | None:
        if self.pooler_config is None:
            return None

        pooling_task = self.pooler_config.task

        if pooling_task is not None:
            if self.pooler_config.task in supported_tasks:
                return self.pooler_config.task
            else:
                raise RuntimeError(
                    f"Unsupported task: {pooling_task!r} "
                    f"Supported tasks: {supported_tasks}"
                )

        if "token_classify" in supported_tasks:
            for architecture in self.architectures:
                if "ForTokenClassification" in architecture:
                    return "token_classify"

        priority: list[PoolingTask] = [
            "embed&token_classify",
            "embed",
            "classify",
            "token_embed",
            "token_classify",
            "plugin",
        ]
        for task in priority:
            if task in supported_tasks:
                return task
        return None