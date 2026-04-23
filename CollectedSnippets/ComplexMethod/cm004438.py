def forward(
        self,
        past_values: Sequence[torch.Tensor],
        window_size: int | None = None,
        future_values: torch.Tensor | None = None,
        forecast_context_len: int | None = None,
        truncate_negative: bool | None = None,
        force_flip_invariance: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> TimesFm2_5OutputForPrediction:
        r"""
        past_values (`Sequence[torch.Tensor]`):
            Past values of the time series that serves as input to the model. Each tensor is a 1D time series.
        window_size (`int`, *optional*):
            Window size of trend + residual decomposition. If `None`, decomposition is not applied.
        future_values (`torch.Tensor`, *optional*):
            Optional future values used to compute the loss.
        forecast_context_len (`int`, *optional*):
            Optional context length override used during forecasting.
        truncate_negative (`bool`, *optional*):
            Whether to clamp outputs to non-negative values. If `None`, defaults to `config.infer_is_positive`.
        force_flip_invariance (`bool`, *optional*):
            Whether to apply the flip-invariance combination. If `None`, defaults to
            `config.force_flip_invariance`.
        """
        forecast_context_len = forecast_context_len or self.context_len
        device = past_values[0].device

        inputs = [ts[-forecast_context_len:] for ts in past_values]
        input_min = torch.min(torch.stack([torch.min(ts) for ts in inputs]))

        if window_size is not None:
            new_inputs: list[torch.Tensor] = []
            for ts in inputs:
                new_inputs.extend(self._timesfm_moving_average(ts, window_size))
            inputs = new_inputs

        if truncate_negative is None:
            truncate_negative = self.config.infer_is_positive
        if force_flip_invariance is None:
            force_flip_invariance = self.config.force_flip_invariance

        input_ts, input_padding = self._preprocess(inputs, context_len=forecast_context_len)
        input_ts = input_ts.to(device)
        input_padding = input_padding.to(device)

        mu_global = input_ts.mean(dim=1, keepdim=True)
        sigma_global = input_ts.std(dim=1, keepdim=True)

        normalized_ts = self.model._revin(input_ts, mu_global, sigma_global, reverse=False)

        pf_outputs, quantile_spreads, model_outputs = self._decode_and_project(normalized_ts, input_padding, **kwargs)

        if force_flip_invariance:
            flipped_pf, flipped_qs, _ = self._decode_and_project(-normalized_ts, input_padding, **kwargs)

            def _flip_quantiles(x: torch.Tensor) -> torch.Tensor:
                return torch.cat([x[..., :1], torch.flip(x[..., 1:], dims=(-1,))], dim=-1)

            pf_outputs = (pf_outputs - _flip_quantiles(flipped_pf)) / 2
            quantile_spreads = (quantile_spreads - _flip_quantiles(flipped_qs)) / 2

        horizon = min(self.horizon_len, pf_outputs.shape[1])
        full_forecast = pf_outputs[:, :horizon, :].clone()

        median_index = min(self.config.decode_index, full_forecast.shape[-1] - 1)
        if self.config.use_continuous_quantile_head:
            max_quantile_horizon = min(horizon, quantile_spreads.shape[1])
            for idx, _ in enumerate(self.config.quantiles, start=1):
                if idx == median_index or idx >= full_forecast.shape[-1]:
                    continue
                full_forecast[:, :max_quantile_horizon, idx] = (
                    quantile_spreads[:, :max_quantile_horizon, idx]
                    - quantile_spreads[:, :max_quantile_horizon, median_index]
                    + full_forecast[:, :max_quantile_horizon, median_index]
                )

        full_predictions = self.model._revin(full_forecast, mu_global, sigma_global, reverse=True)
        decode_index = min(self.config.decode_index, full_predictions.shape[-1] - 1)
        mean_predictions = full_predictions[:, :, decode_index]

        if window_size is not None:
            mean_predictions = mean_predictions[0::2, ...] + mean_predictions[1::2, ...]
            full_predictions = full_predictions[0::2, ...] + full_predictions[1::2, ...]

        if truncate_negative:
            zero = torch.zeros(1, device=mean_predictions.device, dtype=mean_predictions.dtype)
            clamped_mean = torch.maximum(mean_predictions, zero)
            clamped_full = torch.maximum(full_predictions, zero)
            should_clamp = (input_min >= 0).to(mean_predictions.device)
            mean_predictions = torch.where(should_clamp, clamped_mean, mean_predictions)
            full_predictions = torch.where(should_clamp, clamped_full, full_predictions)

        loss = None
        if future_values is not None:
            target_len = future_values.shape[1]
            # Compute loss in normalized space for scale-invariant training.
            # full_forecast is already in normalized space (before denormalization).
            normalized_preds = full_forecast[:, :target_len]
            normalized_targets = self.model._revin(future_values, mu_global, sigma_global, reverse=False)
            normalized_mean_preds = normalized_preds[:, :, decode_index]
            mse_loss = F.mse_loss(normalized_mean_preds, normalized_targets)
            quantile_indices = [i for i in range(normalized_preds.shape[-1]) if i != decode_index]
            if quantile_indices:
                index_tensor = torch.tensor(quantile_indices, device=normalized_preds.device, dtype=torch.long)
                quantile_tensor = torch.index_select(normalized_preds, dim=-1, index=index_tensor)
                quantile_loss = self._quantile_loss(quantile_tensor, normalized_targets)
                loss = mse_loss + quantile_loss
            else:
                loss = mse_loss

        return TimesFm2_5OutputForPrediction(
            last_hidden_state=model_outputs.last_hidden_state,
            hidden_states=model_outputs.hidden_states,
            attentions=model_outputs.attentions,
            mean_predictions=mean_predictions,
            full_predictions=full_predictions,
            loss=loss,
        )