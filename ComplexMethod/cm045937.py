def forward(
        self,
        hidden_states: torch.Tensor,
        input_dimensions: Tuple[int, int],
        head_mask=None,
        output_attentions=False,
        always_partition=False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        if not always_partition:
            self.set_shift_and_window_size(input_dimensions)
        else:
            pass
        height, width = input_dimensions
        batch_size, _, channels = hidden_states.shape
        shortcut = hidden_states

        hidden_states = self.layernorm_before(hidden_states)

        hidden_states = hidden_states.reshape([batch_size, height, width, channels])

        # pad hidden_states to multiples of window size
        hidden_states, pad_values = self.maybe_pad(hidden_states, height, width)

        _, height_pad, width_pad, _ = hidden_states.shape

        # cyclic shift
        if self.shift_size > 0:
            shift_value = (-self.shift_size, -self.shift_size)
            if self.is_export:
                shift_value = torch.tensor(shift_value, dtype=torch.int32)
            shifted_hidden_states = torch.roll(
                hidden_states, shifts=shift_value, dims=(1, 2)
            )
        else:
            shifted_hidden_states = hidden_states

        # partition windows
        hidden_states_windows = window_partition(
            shifted_hidden_states, self.window_size
        )
        hidden_states_windows = hidden_states_windows.reshape(
            [-1, self.window_size * self.window_size, channels]
        )
        attn_mask = self.get_attn_mask(height_pad, width_pad, dtype=hidden_states.dtype)

        attention_outputs = self.attention(
            hidden_states_windows,
            attn_mask,
            head_mask,
            output_attentions=output_attentions,
        )
        attention_output = attention_outputs[0]

        attention_windows = attention_output.reshape(
            [-1, self.window_size, self.window_size, channels]
        )
        shifted_windows = window_reverse(
            attention_windows, self.window_size, height_pad, width_pad
        )
        # reverse cyclic shift
        if self.shift_size > 0:
            shift_value = (self.shift_size, self.shift_size)
            if self.is_export:
                shift_value = torch.tensor(shift_value, dtype=torch.int32)
            attention_windows = torch.roll(
                shifted_windows, shifts=shift_value, dims=(1, 2)
            )
        else:
            attention_windows = shifted_windows

        was_padded = pad_values[3] > 0 or pad_values[5] > 0
        if was_padded:
            attention_windows = attention_windows[:, :height, :width, :].contiguous()

        attention_windows = attention_windows.reshape(
            [batch_size, height * width, channels]
        )
        hidden_states = shortcut + self.drop_path(attention_windows)
        layer_output = self.layernorm_after(hidden_states)
        layer_output = self.intermediate(layer_output)
        layer_output = hidden_states + self.output(layer_output)
        layer_outputs = (
            (layer_output, attention_outputs[1])
            if output_attentions
            else (layer_output,)
        )
        return layer_outputs