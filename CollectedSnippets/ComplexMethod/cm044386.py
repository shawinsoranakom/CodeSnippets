def _update_dropouts(self, model: keras.models.Model) -> keras.models.Model:
        """ Update the saved model with new dropout rates.

        Keras, annoyingly, does not actually change the dropout of the underlying layer, so we need
        to update the rate, then clone the model into a new model and reload weights.

        Parameters
        ----------
        model: :class:`keras.models.Model`
            The loaded saved Keras Model to update the dropout rates for

        Returns
        -------
        :class:`keras.models.Model`
            The loaded Keras Model with the dropout rates updated
        """
        dropouts = {"fc": cfg.fc_dropout(), "gblock": cfg.fc_gblock_dropout()}
        logger.debug("Config dropouts: %s", dropouts)
        updated = False
        for mod in get_all_sub_models(model):
            if not mod.name.startswith("fc_"):
                continue
            key = "gblock" if "gblock" in mod.name else mod.name.split("_")[0]
            rate = dropouts[key]
            log_once = False
            for layer in mod.layers:
                if not isinstance(layer, kl.Dropout):
                    continue
                if layer.rate != rate:
                    logger.debug("Updating dropout rate for %s from %s to %s",
                                 f"{mod.name} - {layer.name}", layer.rate, rate)
                    if not log_once:
                        logger.info("Updating Dropout Rate for '%s' from %s to %s",
                                    mod.name, layer.rate, rate)
                        log_once = True
                    layer.rate = rate
                    updated = True
        if updated:
            logger.debug("Dropout rate updated. Cloning model")
            new_model = keras.models.clone_model(model)
            new_model.set_weights(model.get_weights())
            del model
            model = new_model
        return model