def forward(
        self,
        past_values: torch.Tensor,
        observed_mask: torch.Tensor | None = None,
        output_hidden_states: bool | None = False,
        return_loss: bool = True,
        return_dict: bool | None = None,
        **kwargs,
    ) -> PatchTSMixerForPreTrainingOutput:
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
        return_loss (`bool`,  *optional*):
            Whether to return the loss in the `forward` call.
        """
        return_dict = return_dict if return_dict is not None else self.return_dict

        if self.masked_loss is True:
            loss = torch.nn.MSELoss(reduction="none")
        else:
            loss = torch.nn.MSELoss(reduction="mean")

        # past_values: tensor [batch_size x context_length x num_input_channels]
        model_output = self.model(
            past_values,
            observed_mask=observed_mask,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )  # x.last_hidden_state: [batch_size x nvars x num_patch x d_model]
        if isinstance(model_output, tuple):
            model_output = PatchTSMixerModelOutput(*model_output)

        x_hat = self.head(model_output.last_hidden_state)  # tensor [batch_size x nvars x num_patch x patch_length]

        if return_loss is True:
            loss_val = loss(x_hat, model_output.patch_input)
        else:
            loss_val = None

        # calculate masked_loss
        if self.masked_loss is True and loss_val is not None:
            loss_val = (loss_val.mean(dim=-1) * model_output.mask).sum() / (model_output.mask.sum() + 1e-10)

        if not return_dict:
            return tuple(
                v
                for v in [
                    loss_val,
                    x_hat,
                    model_output.last_hidden_state,
                    model_output.hidden_states,
                ]
            )

        return PatchTSMixerForPreTrainingOutput(
            loss=loss_val,
            prediction_outputs=x_hat,  # tensor [batch_size x nvars x num_patch x patch_length]
            last_hidden_state=model_output.last_hidden_state,  # x: [batch_size x nvars x num_patch x d_model]
            hidden_states=model_output.hidden_states,
        )