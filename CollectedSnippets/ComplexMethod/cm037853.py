def load_weights(self, model: nn.Module, model_config: ModelConfig) -> None:
        from vllm.distributed import get_tensor_model_parallel_rank

        model_weights = model_config.model
        if model_weights_override := model_config.model_weights:
            model_weights = model_weights_override
        local_model_path = model_weights

        rank = get_tensor_model_parallel_rank()
        pattern = os.path.join(
            local_model_path,
            self.pattern.format(rank=rank, part="*"),
        )

        filepaths = []
        if is_s3(local_model_path):
            file_pattern = f"*{self.pattern.format(rank=rank, part='*')}"
            filepaths = s3_glob(path=local_model_path, allow_pattern=[file_pattern])
        else:
            filepaths = glob.glob(pattern)
        if not filepaths:
            # TODO: support un-sharded checkpoints too
            raise ValueError(
                f"Could not find checkpoint files '{pattern}', only "
                f"pre-sharded checkpoints are currently supported!"
            )
        state_dict = self._filter_subtensors(model.state_dict())
        counter_before_loading_weights = time.perf_counter()
        for key, tensor in self.iterate_over_files(filepaths):
            # If loading with LoRA enabled, additional padding may
            # be added to certain parameters. We only load into a
            # narrowed view of the parameter data.
            param_data = state_dict[key].data
            param_shape = state_dict[key].shape
            for dim, size in enumerate(tensor.shape):
                if size < param_shape[dim]:
                    param_data = param_data.narrow(dim, 0, size)
            if tensor.shape != param_shape:
                logger.warning(
                    "loading tensor of shape %s into parameter '%s' of shape %s",
                    tensor.shape,
                    key,
                    param_shape,
                )
            param_data.copy_(tensor)
            state_dict.pop(key)
        counter_after_loading_weights = time.perf_counter()
        logger.info_once(
            "Loading weights took %.2f seconds",
            counter_after_loading_weights - counter_before_loading_weights,
        )
        if state_dict:
            raise ValueError(f"Missing keys {tuple(state_dict)} in loaded state!")