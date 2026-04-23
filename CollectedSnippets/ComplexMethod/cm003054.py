def create_network_inputs(
        self,
        past_values: torch.Tensor,
        past_time_features: torch.Tensor,
        static_categorical_features: torch.Tensor | None = None,
        static_real_features: torch.Tensor | None = None,
        past_observed_mask: torch.Tensor | None = None,
        future_values: torch.Tensor | None = None,
        future_time_features: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Creates the inputs for the network given the past and future values, time features, and static features.

        Args:
            past_values (`torch.Tensor`):
                A tensor of shape `(batch_size, past_length, input_size)` containing the past values.
            past_time_features (`torch.Tensor`):
                A tensor of shape `(batch_size, past_length, num_features)` containing the past time features.
            static_categorical_features (`Optional[torch.Tensor]`):
                An optional tensor of shape `(batch_size, num_categorical_features)` containing the static categorical
                features.
            static_real_features (`Optional[torch.Tensor]`):
                An optional tensor of shape `(batch_size, num_real_features)` containing the static real features.
            past_observed_mask (`Optional[torch.Tensor]`):
                An optional tensor of shape `(batch_size, past_length, input_size)` containing the mask of observed
                values in the past.
            future_values (`Optional[torch.Tensor]`):
                An optional tensor of shape `(batch_size, future_length, input_size)` containing the future values.

        Returns:
            A tuple containing the following tensors:
            - reshaped_lagged_sequence (`torch.Tensor`): A tensor of shape `(batch_size, sequence_length, num_lags *
              input_size)` containing the lagged subsequences of the inputs.
            - features (`torch.Tensor`): A tensor of shape `(batch_size, sequence_length, num_features)` containing the
              concatenated static and time features.
            - loc (`torch.Tensor`): A tensor of shape `(batch_size, input_size)` containing the mean of the input
              values.
            - scale (`torch.Tensor`): A tensor of shape `(batch_size, input_size)` containing the std of the input
              values.
            - static_feat (`torch.Tensor`): A tensor of shape `(batch_size, num_static_features)` containing the
              concatenated static features.
        """
        # time feature
        time_feat = (
            torch.cat(
                (
                    past_time_features[:, self._past_length - self.config.context_length :, ...],
                    future_time_features,
                ),
                dim=1,
            )
            if future_values is not None
            else past_time_features[:, self._past_length - self.config.context_length :, ...]
        )

        # target
        if past_observed_mask is None:
            past_observed_mask = torch.ones_like(past_values)

        context = past_values[:, -self.config.context_length :]
        observed_context = past_observed_mask[:, -self.config.context_length :]
        _, loc, scale = self.scaler(context, observed_context)

        inputs = (
            (torch.cat((past_values, future_values), dim=1) - loc) / scale
            if future_values is not None
            else (past_values - loc) / scale
        )

        # static features
        log_abs_loc = loc.abs().log1p() if self.config.input_size == 1 else loc.squeeze(1).abs().log1p()
        log_scale = scale.log() if self.config.input_size == 1 else scale.squeeze(1).log()
        static_feat = torch.cat((log_abs_loc, log_scale), dim=1)

        if static_real_features is not None:
            static_feat = torch.cat((static_real_features, static_feat), dim=1)
        if static_categorical_features is not None:
            embedded_cat = self.embedder(static_categorical_features)
            static_feat = torch.cat((embedded_cat, static_feat), dim=1)
        expanded_static_feat = static_feat.unsqueeze(1).expand(-1, time_feat.shape[1], -1)

        # all features
        features = torch.cat((expanded_static_feat, time_feat), dim=-1)

        # lagged features
        subsequences_length = (
            self.config.context_length + self.config.prediction_length
            if future_values is not None
            else self.config.context_length
        )
        lagged_sequence = self.get_lagged_subsequences(sequence=inputs, subsequences_length=subsequences_length)
        lags_shape = lagged_sequence.shape
        reshaped_lagged_sequence = lagged_sequence.reshape(lags_shape[0], lags_shape[1], -1)

        if reshaped_lagged_sequence.shape[1] != time_feat.shape[1]:
            raise ValueError(
                f"input length {reshaped_lagged_sequence.shape[1]} and time feature lengths {time_feat.shape[1]} does not match"
            )
        return reshaped_lagged_sequence, features, loc, scale, static_feat