def _get_train_loader(self) -> TrainLoader:
        """Get the loaders for training the model

        Returns
        -------
        The loaders for feeding the model's training loop
        """
        input_sizes = [x[1] for x in self._model.input_shapes]
        assert len(set(input_sizes)) == 1, f"Multiple input sizes not supported. Got {input_sizes}"

        out_sizes = [x[1] for x in self._model.output_shapes if x[-1] != 1]
        num_sides = len(self._plugin.config.folders)
        assert len(out_sizes) % num_sides == 0, (
            f"Output count ({len(out_sizes)}) doesn't match number of inputs ({num_sides})")
        split = len(out_sizes) // num_sides
        split_sizes = [out_sizes[x:x+split] for x in range(0, len(out_sizes), split)]
        assert len(set(out_sizes)) == len(set(split_sizes[0])), "Sizes for each output must match"

        retval = TrainLoader(input_sizes[0],
                             tuple(split_sizes[0]),
                             self._model.color_order,
                             self._plugin.config,
                             self._plugin.sampler)
        logger.debug("[Trainer] data loader: %s", retval)
        return retval