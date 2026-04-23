def forward(
        self,
        past_values: torch.Tensor,
        target_values: torch.Tensor | None = None,
        output_hidden_states: bool | None = False,
        return_loss: bool = True,
        return_dict: bool | None = None,
        **kwargs,
    ) -> PatchTSMixerForRegressionOutput:
        r"""
        past_values (`torch.FloatTensor` of shape `(batch_size, seq_length, num_input_channels)`):
            Context values of the time series. For a pretraining task, this denotes the input time series to predict
            the masked portion. For a forecasting task, this denotes the history/past time series values. Similarly,
            for classification or regression tasks, it denotes the appropriate context values of the time series.

            For univariate time series, `num_input_channels` dimension should be 1. For multivariate time series, it is
            greater than 1.
        target_values (`torch.FloatTensor` of shape `(batch_size, target_len, num_input_channels)` for forecasting,
            `(batch_size, num_targets)` for regression, or `(batch_size,)` for classification, *optional*):
            Target values of the time series, that serve as labels for the model. The `target_values` is what the
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

        if self.loss == "mse":
            loss = nn.MSELoss(reduction="mean")
        elif self.loss == "nll":
            loss = nll
        else:
            raise ValueError("Invalid loss function: Allowed values: mse and nll")

        return_dict = return_dict if return_dict is not None else self.return_dict
        model_output = self.model(
            past_values,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )  # model_output: [batch_size x nvars x num_patch x d_model]
        if isinstance(model_output, tuple):
            model_output = PatchTSMixerModelOutput(*model_output)

        if self.inject_scale is not None:
            model_output.last_hidden_state = self.inject_scale(
                model_output.last_hidden_state,
                loc=model_output.loc,
                scale=model_output.scale,
            )  # x: [batch_size x nvars x num_patch x d_model]

        y_hat = self.head(model_output.last_hidden_state)  # [batch_size x num_targets]

        if target_values is not None and return_loss is True:
            if self.distribution_output:
                if self.distribution_output == "negative_binomial" and torch.any(target_values < 0):
                    raise Exception("target_values cannot be negative for negative_binomial distribution.")
                distribution = self.distribution_output.distribution(y_hat)
                # y_hat should be a 2-tuple, each with dimension [bs, num_targets]
                y_hat = tuple(item.view(-1, self.config.num_targets) for item in y_hat)
                loss_val = loss(distribution, target_values)
                # take average of the loss
                loss_val = weighted_average(loss_val)
            else:
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

        return PatchTSMixerForRegressionOutput(
            loss=loss_val,
            regression_outputs=y_hat,  # tensor [batch_size x num_targets]
            last_hidden_state=model_output.last_hidden_state,  # [batch_size x nvars x num_patch x d_model]
            hidden_states=model_output.hidden_states,
        )