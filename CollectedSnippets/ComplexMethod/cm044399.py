def build(self) -> None:
        """Build the model and assign to :attr:`model`.

        Within the defined strategy scope, either builds the model from scratch or loads an
        existing model if one exists.

        If running inference, then the model is built only for the required side to perform the
        swap function, otherwise  the model is then compiled with the optimizer and chosen
        loss function(s).

        Finally, a model summary is outputted to the logger at verbose level.
        """
        is_summary = hasattr(self._args, "summary") and self._args.summary
        if self._io.model_exists:
            model = self.io.load()
            if self._is_predict:
                inference = Inference(model, self._args.swap_model)
                self._model = inference()
            else:
                self._model = model
        else:
            self._validate_input_shape()
            inputs = self._get_inputs()
            if not self._settings.use_mixed_precision and not is_summary:
                # Store layer names which can be switched to mixed precision
                model, mp_layers = self._settings.get_mixed_precision_layers(self.build_model,
                                                                             inputs)
                self._state.add_mixed_precision_layers(mp_layers)
                self._model = model
            else:
                self._model = self.build_model(inputs)
        if not is_summary and not self._is_predict:
            self._compile_model()
        self._output_summary()