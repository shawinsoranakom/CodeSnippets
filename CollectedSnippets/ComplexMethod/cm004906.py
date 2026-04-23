def forward(
        self,
        past_values: Sequence[torch.Tensor],
        freq: Sequence[torch.Tensor | int] | None = None,
        window_size: int | None = None,
        future_values: torch.Tensor | None = None,
        forecast_context_len: int | None = None,
        return_forecast_on_context: bool = False,
        truncate_negative: bool = False,
        **kwargs: Unpack[TransformersKwargs],
    ) -> TimesFmOutputForPrediction:
        r"""
        past_values (`torch.FloatTensor` of shape `(batch_size, sequence_length)`):
            Past values of the time series that serves as input to the model.
        freq (`torch.LongTensor` of shape `(batch_size,)`):
            Frequency indices for the time series data.
        window_size (`int`, *optional*):
            Window size of trend + residual decomposition. If None then we do not do decomposition.
        future_values (`torch.Tensor`, *optional*):
            Optional future time series values to be used for loss computation.
        forecast_context_len (`int`, *optional*):
            Optional max context length.
        return_forecast_on_context (`bool`, *optional*):
            True to return the forecast on the context when available, i.e. after the first input patch.
        truncate_negative (`bool`, *optional*):
            Truncate to only non-negative values if any of the contexts have non-negative values,
            otherwise do nothing.

        Example:

        ```python
        >>> from transformers import TimesFmModelForPrediction

        >>> model = TimesFmModelForPrediction.from_pretrained("google/timesfm-2.0-500m-pytorch")

        >>> forecast_input = [torch.linspace(0, 20, 100).sin(), torch.linspace(0, 20, 200).sin(), torch.linspace(0, 20, 400).sin()]
        >>> frequency_input = torch.tensor([0, 1, 2], dtype=torch.long)

        >>> # Generate
        >>> with torch.no_grad():
        >>>     outputs = model(past_values=forecast_input, freq=frequency_input, return_dict=True)
        >>>     point_forecast_conv = outputs.mean_predictions
        >>>     quantile_forecast_conv = outputs.full_predictions
        ```
        """
        if forecast_context_len is None:
            fcontext_len = self.context_len
        else:
            fcontext_len = forecast_context_len

        device = past_values[0].device

        inputs = [ts[-fcontext_len:] for ts in past_values]
        inp_min = torch.min(torch.stack([torch.min(ts) for ts in inputs]))

        if window_size is not None:
            new_inputs = []
            new_freqs = []
            for i, ts in enumerate(inputs):
                new_inputs.extend(self._timesfm_moving_average(ts, window_size))
                if freq is not None:
                    new_freqs.extend([freq[i]] * 2)
            inputs = new_inputs
            if freq is not None:
                freq = new_freqs

        if freq is None:
            logger.info("No frequency provided via `freq`. Default to high (0).")
            freq = [0] * len(inputs)

        input_ts, input_padding, inp_freq = self._preprocess(inputs, freq)
        input_ts = input_ts.to(device)
        input_padding = input_padding.to(device)
        inp_freq = inp_freq.to(device)

        final_out = input_ts
        context_len = final_out.shape[1]
        full_outputs = []

        if input_padding.shape[1] != final_out.shape[1] + self.horizon_len:
            raise ValueError(
                "Length of paddings must match length of input + horizon_len:"
                f" {input_padding.shape[1]} != {final_out.shape[1]} + {self.horizon_len}"
            )
        output_patch_len = self.config.horizon_length

        num_decode_patches = (self.horizon_len + output_patch_len - 1) // output_patch_len
        for step_index in range(num_decode_patches):
            current_padding = input_padding[:, 0 : final_out.shape[1]]
            input_ts = final_out[:, -fcontext_len:]
            input_padding = current_padding[:, -fcontext_len:]
            decoder_output: TimesFmOutput = self.decoder(
                past_values=input_ts,
                past_values_padding=input_padding,
                freq=inp_freq,
                **kwargs,
            )
            fprop_outputs = self._postprocess_output(
                decoder_output.last_hidden_state,
                (decoder_output.loc, decoder_output.scale),
            )

            if return_forecast_on_context and step_index == 0:
                new_full_ts = fprop_outputs[:, :-1, : self.config.patch_length, :]
                new_full_ts = new_full_ts.reshape(new_full_ts.size(0), -1, new_full_ts.size(3))
                full_outputs.append(new_full_ts)

            new_ts = fprop_outputs[:, -1, :output_patch_len, 0]
            new_full_ts = fprop_outputs[:, -1, :output_patch_len, :]
            full_outputs.append(new_full_ts)
            final_out = torch.concatenate([final_out, new_ts], axis=-1)

        if return_forecast_on_context:
            full_outputs = torch.concatenate(full_outputs, axis=1)[
                :, : (context_len - self.config.patch_length + self.horizon_len), :
            ]
        else:
            full_outputs = torch.concatenate(full_outputs, axis=1)[:, 0 : self.horizon_len, :]

        mean_outputs = full_outputs[:, :, 0]
        if window_size is not None:
            mean_outputs = mean_outputs[0::2, ...] + mean_outputs[1::2, ...]
            full_outputs = full_outputs[0::2, ...] + full_outputs[1::2, ...]
        if inp_min >= 0 and truncate_negative:
            mean_outputs = torch.maximum(mean_outputs, 0.0)
            full_outputs = torch.maximum(full_outputs, 0.0)

        loss = None
        if future_values is not None:
            mse_loss = F.mse_loss(mean_outputs, future_values)
            quantile_loss = self._quantile_loss(full_outputs[:, :, 1:], future_values)
            loss = mse_loss + quantile_loss

        return TimesFmOutputForPrediction(
            last_hidden_state=decoder_output.last_hidden_state,
            attentions=decoder_output.attentions,
            hidden_states=decoder_output.hidden_states,
            mean_predictions=mean_outputs,
            full_predictions=full_outputs,
            loss=loss,
        )