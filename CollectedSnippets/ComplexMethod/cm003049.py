def forward(
        self,
        past_values: torch.Tensor,
        observed_mask: torch.Tensor | None = None,
        future_values: torch.Tensor | None = None,
        output_hidden_states: bool | None = False,
        return_loss: bool = True,
        return_dict: bool | None = None,
        **kwargs,
    ) -> PatchTSMixerForPredictionOutput:
        r"""
        past_values (`torch.FloatTensor` of shape `(batch_size, seq_length, num_input_channels)`):
            Context values of the time series. For a pretraining task, this denotes the input time series to predict
            the masked portion. For a forecasting task, this denotes the history/past time series values. Similarly,
            for classification or regression tasks, it denotes the appropriate context values of the time series.

            For univariate time series, `num_input_channels` dimension should be 1. For multivariate time series, it is
            greater than 1.
        observed_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length, num_input_channels)`, *optional*):
            Boolean mask to indicate which `past_values` were observed and which were missing. Mask values selected
            in `[0, 1]`:
            - 1 for values that are **observed**,
            - 0 for values that are **missing** (i.e. NaNs that were replaced by zeros).
        future_values (`torch.FloatTensor` of shape `(batch_size, target_len, num_input_channels)` for forecasting,:
            `(batch_size, num_targets)` for regression, or `(batch_size,)` for classification, *optional*):
            Target values of the time series, that serve as labels for the model. The `future_values` is what the
            Transformer needs during training to learn to output, given the `past_values`. Note that, this is NOT
            required for a pretraining task.

            For a forecasting task, the shape is be `(batch_size, target_len, num_input_channels)`. Even if we want
            to forecast only specific channels by setting the indices in `prediction_channel_indices` parameter,
            pass the target data with all channels, as channel Filtering for both prediction and target will be
            manually applied before the loss computation.
        return_loss (`bool`,  *optional*):
            Whether to return the loss in the `forward` call.
        """
        if self.loss == "mse":
            loss = nn.MSELoss(reduction="mean")
        elif self.loss == "nll":
            loss = nll
        else:
            raise ValueError("Invalid loss function: Allowed values: mse and nll")

        return_dict = return_dict if return_dict is not None else self.return_dict

        # past_values: tensor [batch_size x context_length x num_input_channels]
        model_output = self.model(
            past_values,
            observed_mask=observed_mask,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )  # model_output: [batch_size x nvars x num_patch x d_model]
        if isinstance(model_output, tuple):
            model_output = PatchTSMixerModelOutput(*model_output)

        # tensor [batch_size x prediction_length x num_input_channels]
        y_hat = self.head(model_output.last_hidden_state)

        loss_val = None
        if self.prediction_channel_indices is not None:
            if self.distribution_output:
                distribution = self.distribution_output.distribution(
                    y_hat,
                    loc=model_output.loc[..., self.prediction_channel_indices],
                    scale=model_output.scale[..., self.prediction_channel_indices],
                )
                if future_values is not None and return_loss is True:
                    loss_val = loss(
                        distribution,
                        future_values[..., self.prediction_channel_indices],
                    )
                    # take average of the loss
                    loss_val = weighted_average(loss_val)
            else:
                y_hat = (
                    y_hat * model_output.scale[..., self.prediction_channel_indices]
                    + model_output.loc[..., self.prediction_channel_indices]
                )
                if future_values is not None and return_loss is True:
                    loss_val = loss(y_hat, future_values[..., self.prediction_channel_indices])
        else:
            if self.distribution_output:
                distribution = self.distribution_output.distribution(
                    y_hat, loc=model_output.loc, scale=model_output.scale
                )
                if future_values is not None and return_loss is True:
                    loss_val = loss(distribution, future_values)
                    loss_val = weighted_average(loss_val)
            else:
                y_hat = y_hat * model_output.scale + model_output.loc
                if future_values is not None and return_loss is True:
                    loss_val = loss(y_hat, future_values)

        if self.prediction_channel_indices is not None:
            loc = model_output.loc[..., self.prediction_channel_indices]
            scale = model_output.scale[..., self.prediction_channel_indices]
        else:
            loc = model_output.loc
            scale = model_output.scale

        if not return_dict:
            return tuple(
                v
                for v in [
                    loss_val,
                    y_hat,
                    model_output.last_hidden_state,
                    model_output.hidden_states,
                    loc,
                    scale,
                ]
            )

        return PatchTSMixerForPredictionOutput(
            loss=loss_val,
            prediction_outputs=y_hat,  # tensor [batch_size x prediction_length x num_input_channels]
            last_hidden_state=model_output.last_hidden_state,  # x: [batch_size x nvars x num_patch x d_model]
            hidden_states=model_output.hidden_states,
            loc=loc,
            scale=scale,
        )