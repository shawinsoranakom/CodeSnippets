def __call__(self) -> keras.models.Model:
        """Obtain the inference model.

        Returns
        -------
        The built Keras inference model for the requested swap side
        """
        built = {self._input.name: self._input}
        to_build = {k: v for k, v in self._valid_layer_inputs.items()
                    if k in self._filtered_layers}
        logger.debug("[Inference] Building inference model from '%s' with layers %s",
                     self._input.name, [k.name for k in to_build])
        for layer, inputs in to_build.items():
            name = layer.name
            input_names = [i.name for i in inputs]
            logger.debug("[Inference] Building layer '%s' with inputs %s", name, input_names)
            assert all(i in built for i in input_names)
            input_layers = [built[n] for n in input_names]
            built[layer.name] = layer(input_layers if len(input_layers) > 1 else input_layers[0])

        output = built[self._output.name]
        retval = keras.Model(inputs=self._input, outputs=output, name=self._name)
        logger.debug("[Inference] Built model: %s", retval.name)
        return retval