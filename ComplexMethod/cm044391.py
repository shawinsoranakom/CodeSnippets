def load(self, model_exists: bool) -> None:
        """ Load weights for newly created models, or output warning for pre-existing models.

        Parameters
        ----------
        model_exists: bool
            ``True`` if a model pre-exists and is being resumed, ``False`` if this is a new model
        """
        if not self._weights_file:
            logger.debug("No weights file provided. Not loading weights.")
            return
        if model_exists and self._weights_file:
            logger.warning("Ignoring weights file '%s' as this model is resuming.",
                           self._weights_file)
            return

        weights_models = self._get_weights_model()
        all_models = get_all_sub_models(self._model)
        loaded_ops = 0
        skipped_ops = 0

        for model_name in self._load_layers:
            sub_model = next((lyr for lyr in all_models if lyr.name == model_name), None)
            sub_weights = next((lyr for lyr in weights_models if lyr.name == model_name), None)

            if not sub_model or not sub_weights:
                msg = f"Skipping layer {model_name} as not in "
                msg += "current_model." if not sub_model else f"weights '{self._weights_file}.'"
                logger.warning(msg)
                continue

            logger.info("Loading weights for layer '%s'", model_name)
            skipped_ops = 0
            loaded_ops = 0
            for layer in sub_model.layers:
                success = self._load_layer_weights(layer, sub_weights, model_name)
                if success == 0:
                    skipped_ops += 1
                elif success == 1:
                    loaded_ops += 1

        del weights_models

        if loaded_ops == 0:
            raise FaceswapError(f"No weights were succesfully loaded from your weights file: "
                                f"'{self._weights_file}'. Please check and try again.")
        if skipped_ops > 0:
            logger.warning("%s weight(s) were unable to be loaded for your model. This is most "
                           "likely because the weights you are trying to load were trained with "
                           "different settings than you have set for your current model.",
                           skipped_ops)