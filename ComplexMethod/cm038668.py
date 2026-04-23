def _verify_pooling_task(self, request: PoolingRequest) -> str:
        if getattr(request, "dimensions", None) is not None:
            raise ValueError("dimensions is currently not supported")

        if request.task is None:
            request.task = self.pooling_task

        if isinstance(request, IOProcessorRequest):
            request.task = "plugin"

        assert request.task is not None
        pooling_task = request.task

        # plugin task uses io_processor.parse_request to verify inputs
        if pooling_task != "plugin" and pooling_task != self.pooling_task:
            if pooling_task not in self.supported_tasks:
                raise ValueError(
                    f"Unsupported task: {pooling_task!r} "
                    f"Supported tasks: {self.supported_tasks}"
                )
            else:
                raise ValueError(
                    "Try switching the model's pooling_task "
                    f"via --pooler-config.task {request.task}."
                )

        if pooling_task == "plugin" and "plugin" not in self.io_processors:
            raise ValueError(
                "No IOProcessor plugin installed. Please refer "
                "to the documentation and to the "
                "'prithvi_geospatial_mae_io_processor' "
                "offline inference example for more details."
            )

        return pooling_task