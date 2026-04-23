def _get_output_layer(self, model: keras.models.Model) -> keras.Layer:
        """Obtain the layer that acts as the output for the swap direction of the model

        Parameters
        ----------
        model
            The faceswap model that is to be converted for inference

        Returns
        -------
        The layer that acts as output for the model. This will either be a layer unique to the swap
        side, if split decoders, or the shared output layer if shared decoder
        """
        history: list[node.KerasHistory] = [t._keras_history  # pylint:disable=protected-access
                                            for t in model.output]
        logger.debug("[Inference] '%s' output history: %s", model.name, history)

        layers = [h.operation for h in history]
        outputs_count = len(layers)
        layer_count = len(set(o.name for o in layers))
        logger.debug("[Inference] '%s' outputs count: %s, output layer count: %s",
                     model.name, outputs_count, layer_count)
        assert layer_count in (1, 2), f"Unexpected output layers count: {layer_count}"

        if layer_count == 1:
            retval = layers[0]
        else:
            split = outputs_count // 2
            out_layers = layers[:split] if self._side_idx == 0 else layers[split:]
            out_layer_count = len(set(o.name for o in out_layers))
            assert out_layer_count == 1, f"Unexpected output layer count: {out_layer_count}"
            retval = out_layers[0]

        logger.debug("[Inference] '%s' output layer for side index %s: '%s'",
                     model.name, self._side_idx, retval.name)

        return retval