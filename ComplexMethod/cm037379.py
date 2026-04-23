def reload_weights(
        self,
        weights_iterator: Iterable[tuple[str, torch.Tensor]] | None = None,
        weights_path: str | None = None,
        is_checkpoint_format: bool = True,
    ) -> None:
        """
        Reload weights from a weights iterator or from disk

        :param weights_iterator: weights to load into model
        :param weights_path: path to load weights from if weights_iterator is not
            provided. Use path of original model if neither is provided.
        :param is_checkpoint_format: set to False if weights have already been processed
            into kernel format (repacking, renaming, etc.)
        """
        # TODO(@kylesayrs): generalize to all runners and loaders
        # argument validation
        if weights_iterator is None and not is_checkpoint_format:
            logger.warning(
                "Reloading from disk means that weights will be in checkpoint format. "
                "Please use `is_checkpoint_format=True` "
                "to avoid weight reloading errors"
            )

        model = self.get_model()
        weights_to_load = {name for name, _ in model.named_parameters()}
        counter_before_reloading = time.perf_counter()

        # load weights from disk if none are provided
        if weights_iterator is None:
            model_loader = get_model_loader(self.load_config)
            if not hasattr(model_loader, "get_all_weights"):
                raise NotImplementedError(
                    f"Model reloading with `{self.load_config.load_format}` format"
                )

            if weights_path is not None:
                self.model_config.model = weights_path
            weights_iterator = model_loader.get_all_weights(self.model_config, model)
            weights_iterator = cast(
                Iterable[tuple[str, torch.Tensor]], weights_iterator
            )

        # begin loading weights
        logger.info_once("Reloading weights inplace...")
        if is_checkpoint_format:
            # load weights from checkpoint/ original model format
            initialize_layerwise_reload(model)
            loaded_weights = model.load_weights(weights_iterator)
            finalize_layerwise_reload(model, self.model_config)

        else:
            # load weights from kernel format
            logger.warning_once(
                "Reloading with `is_checkpoint_format=True` requires that "
                "weights be in kernel format and already sharded",
            )
            loaded_weights = set()
            for name, loaded_weight in weights_iterator:
                param = model.get_parameter(name)  # TODO: buffers?
                param.copy_(loaded_weight)
                loaded_weights.add(name)

        # logging and validation
        counter_after_reloading = time.perf_counter()
        diff_seconds = counter_after_reloading - counter_before_reloading
        logger.info_once(
            "Reloading and processing weights took %.2f seconds",
            diff_seconds,
        )
        if self.model_config.quantization is None and loaded_weights is not None:
            weights_not_loaded = weights_to_load - loaded_weights
            if weights_not_loaded:
                logger.warning(
                    "Following weights were not loaded from checkpoint: %s",
                    weights_not_loaded,
                )