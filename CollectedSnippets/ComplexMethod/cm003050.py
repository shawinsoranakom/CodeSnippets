def forward(
        self,
        past_values: torch.Tensor,
        target_values: torch.Tensor | None = None,
        output_hidden_states: bool | None = False,
        return_loss: bool = True,
        return_dict: bool | None = None,
        **kwargs,
    ) -> PatchTSMixerForTimeSeriesClassificationOutput:
        r"""
        past_values (`torch.FloatTensor` of shape `(batch_size, seq_length, num_input_channels)`):
            Context values of the time series. For a pretraining task, this denotes the input time series to predict
            the masked portion. For a forecasting task, this denotes the history/past time series values. Similarly,
            for classification or regression tasks, it denotes the appropriate context values of the time series.

            For univariate time series, `num_input_channels` dimension should be 1. For multivariate time series, it is
            greater than 1.
        target_values (`torch.FloatTensor` of shape `(batch_size, target_len, num_input_channels)` for forecasting,
            `(batch_size, num_targets)` for regression, or `(batch_size,)` for classification, *optional*):
            Target
            values of the time series, that serve as labels for the model. The `target_values` is what the
            Transformer needs during training to learn to output, given the `past_values`. Note that, this is NOT
            required for a pretraining task.

            For a forecasting task, the shape is be `(batch_size, target_len, num_input_channels)`. Even if we want
            to forecast only specific channels by setting the indices in `prediction_channel_indices` parameter,
            pass the target data with all channels, as channel Filtering for both prediction and target will be
            manually applied before the loss computation.

            For a classification task, it has a shape of `(batch_size,)`.

            For a regression task, it has a shape of `(batch_size, num_targets)`.
        return_loss (`bool`, *optional*):
            Whether to return the loss in the `forward` call.
        """

        loss = torch.nn.CrossEntropyLoss()

        return_dict = return_dict if return_dict is not None else self.return_dict

        model_output = self.model(
            past_values,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )  # x: [batch_size x nvars x num_patch x d_model]
        if isinstance(model_output, tuple):
            model_output = PatchTSMixerModelOutput(*model_output)

        if self.inject_scale is not None:
            model_output.last_hidden_state = self.inject_scale(
                model_output.last_hidden_state,
                loc=model_output.loc,
                scale=model_output.scale,
            )  # x: [batch_size x nvars x num_patch x d_model]

        y_hat = self.head(model_output.last_hidden_state)  # tensor [batch_size x n_labels]

        if target_values is not None and return_loss is True:
            loss_val = loss(y_hat, target_values)
        else:
            loss_val = None

        if not return_dict:
            return tuple(
                v
                for v in [
                    loss_val,
                    y_hat,
                    model_output.last_hidden_state,
                    model_output.hidden_states,
                ]
            )

        return PatchTSMixerForTimeSeriesClassificationOutput(
            loss=loss_val,
            prediction_outputs=y_hat,  # tensor [batch_size x n_labels]
            last_hidden_state=model_output.last_hidden_state,  # x: [batch_size x nvars x num_patch x d_model]
            hidden_states=model_output.hidden_states,
        )