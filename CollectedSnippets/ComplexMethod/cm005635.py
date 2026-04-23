def __call__(self, inputs, *args, num_workers=None, batch_size=None, **kwargs):
        if args:
            logger.warning(f"Ignoring args : {args}")

        # Detect if inputs are a chat-style input(s) and cast as `Chat` or list of `Chat`
        container_types = (list, tuple, types.GeneratorType)
        if is_torch_available():
            container_types = (*container_types, KeyDataset)
        if isinstance(inputs, container_types):
            if isinstance(inputs, types.GeneratorType):
                inputs = list(inputs)
            if is_valid_message(inputs[0]):
                inputs = Chat(inputs)
            elif isinstance(inputs[0], (list, tuple)) and all(chat and is_valid_message(chat[0]) for chat in inputs):
                inputs = [Chat(chat) for chat in inputs]

        if num_workers is None:
            if self._num_workers is None:
                num_workers = 0
            else:
                num_workers = self._num_workers
        if batch_size is None:
            if self._batch_size is None:
                batch_size = 1
            else:
                batch_size = self._batch_size

        preprocess_params, forward_params, postprocess_params = self._sanitize_parameters(**kwargs)

        # Fuse __init__ params and __call__ params without modifying the __init__ ones.
        preprocess_params = {**self._preprocess_params, **preprocess_params}
        forward_params = {**self._forward_params, **forward_params}
        postprocess_params = {**self._postprocess_params, **postprocess_params}

        self.call_count += 1
        if self.call_count > 10 and self.device.type == "cuda":
            logger.warning_once(
                "You seem to be using the pipelines sequentially on GPU. In order to maximize efficiency please use a"
                " dataset",
            )

        is_dataset = Dataset is not None and isinstance(inputs, Dataset)
        is_generator = isinstance(inputs, types.GeneratorType)
        is_list = isinstance(inputs, list)

        is_iterable = is_dataset or is_generator or is_list
        can_use_iterator = is_dataset or is_generator or is_list

        if is_list:
            if can_use_iterator:
                final_iterator = self.get_iterator(
                    inputs, num_workers, batch_size, preprocess_params, forward_params, postprocess_params
                )
                outputs = list(final_iterator)
                return outputs
            else:
                return self.run_multi(inputs, preprocess_params, forward_params, postprocess_params)
        elif can_use_iterator:
            return self.get_iterator(
                inputs, num_workers, batch_size, preprocess_params, forward_params, postprocess_params
            )
        elif is_iterable:
            return self.iterate(inputs, preprocess_params, forward_params, postprocess_params)
        elif isinstance(self, ChunkPipeline):
            return next(
                iter(
                    self.get_iterator(
                        [inputs], num_workers, batch_size, preprocess_params, forward_params, postprocess_params
                    )
                )
            )
        else:
            return self.run_single(inputs, preprocess_params, forward_params, postprocess_params)