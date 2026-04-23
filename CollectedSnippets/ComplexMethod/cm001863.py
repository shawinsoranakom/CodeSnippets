def check_module(
        self,
        task,
        params=None,
        output_hidden_states=True,
    ):
        config = PatchTSMixerConfig(**params)
        if task == "forecast":
            mdl = PatchTSMixerForPrediction(config)
            target_input = self.__class__.correct_forecast_output
            if config.prediction_channel_indices is not None:
                target_output = self.__class__.correct_sel_forecast_output
            else:
                target_output = target_input
            ref_samples = target_output.unsqueeze(1).expand(-1, config.num_parallel_samples, -1, -1)
            ground_truth_arg = "future_values"
            output_predictions_arg = "prediction_outputs"
        elif task == "classification":
            mdl = PatchTSMixerForTimeSeriesClassification(config)
            target_input = self.__class__.correct_classification_classes
            target_output = self.__class__.correct_classification_output
            ground_truth_arg = "target_values"
            output_predictions_arg = "prediction_outputs"
        elif task == "regression":
            mdl = PatchTSMixerForRegression(config)
            target_input = self.__class__.correct_regression_output
            target_output = self.__class__.correct_regression_output
            ref_samples = target_output.unsqueeze(1).expand(-1, config.num_parallel_samples, -1)
            ground_truth_arg = "target_values"
            output_predictions_arg = "regression_outputs"
        elif task == "pretrain":
            mdl = PatchTSMixerForPretraining(config)
            target_input = None
            target_output = self.__class__.correct_pretrain_output
            ground_truth_arg = None
            output_predictions_arg = "prediction_outputs"
        else:
            print("invalid task")

        enc_output = self.__class__.enc_output

        if target_input is None:
            output = mdl(self.__class__.data, output_hidden_states=output_hidden_states)
        else:
            output = mdl(
                self.__class__.data,
                **{
                    ground_truth_arg: target_input,
                    "output_hidden_states": output_hidden_states,
                },
            )

        prediction_outputs = getattr(output, output_predictions_arg)
        if isinstance(prediction_outputs, tuple):
            for t in prediction_outputs:
                self.assertEqual(t.shape, target_output.shape)
        else:
            self.assertEqual(prediction_outputs.shape, target_output.shape)

        self.assertEqual(output.last_hidden_state.shape, enc_output.shape)

        if output_hidden_states is True:
            self.assertEqual(len(output.hidden_states), params["num_layers"])

        else:
            self.assertEqual(output.hidden_states, None)

        self.assertEqual(output.loss.item() < np.inf, True)

        if config.loss == "nll" and task in ["forecast", "regression"]:
            samples = mdl.generate(self.__class__.data)
            self.assertEqual(samples.sequences.shape, ref_samples.shape)