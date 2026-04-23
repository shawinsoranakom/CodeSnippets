def forward(self, input, hx=None):
        """
        Runs the forward pass.
        """
        self._update_flat_weights()

        num_directions = 2 if self.bidirectional else 1
        orig_input = input

        if isinstance(orig_input, PackedSequence):
            input, batch_sizes, sorted_indices, unsorted_indices = input
            max_batch_size = batch_sizes[0]
            # script() is unhappy when max_batch_size is different type in cond branches, so we duplicate
            if hx is None:
                hx = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    self.hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
            else:
                # Each batch of the hidden state should match the input sequence that
                # the user believes he/she is passing in.
                hx = self.permute_hidden(hx, sorted_indices)
        else:
            batch_sizes = None
            if input.dim() not in (2, 3):
                raise ValueError(
                    f"RNN: Expected input to be 2D or 3D, got {input.dim()}D tensor instead"
                )
            is_batched = input.dim() == 3
            batch_dim = 0 if self.batch_first else 1
            if not is_batched:
                input = input.unsqueeze(batch_dim)
                if hx is not None:
                    if hx.dim() != 2:
                        raise RuntimeError(
                            f"For unbatched 2-D input, hx should also be 2-D but got {hx.dim()}-D tensor"
                        )
                    hx = hx.unsqueeze(1)
            else:
                if hx is not None and hx.dim() != 3:
                    raise RuntimeError(
                        f"For batched 3-D input, hx should also be 3-D but got {hx.dim()}-D tensor"
                    )
            max_batch_size = input.size(0) if self.batch_first else input.size(1)
            sorted_indices = None
            unsorted_indices = None
            if hx is None:
                hx = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    self.hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
            else:
                # Each batch of the hidden state should match the input sequence that
                # the user believes he/she is passing in.
                hx = self.permute_hidden(hx, sorted_indices)

        if hx is None:
            raise AssertionError("hx must not be None")
        self.check_forward_args(input, hx, batch_sizes)
        if self.mode != "RNN_TANH" and self.mode != "RNN_RELU":
            raise AssertionError(f"mode must be RNN_TANH or RNN_RELU, got {self.mode}")
        if batch_sizes is None:
            if self.mode == "RNN_TANH":
                # pyrefly: ignore [no-matching-overload]
                result = _VF.rnn_tanh(
                    input,
                    hx,
                    self._flat_weights,  # type: ignore[arg-type]
                    self.bias,
                    self.num_layers,
                    self.dropout,
                    self.training,
                    self.bidirectional,
                    self.batch_first,
                )
            else:
                # pyrefly: ignore [no-matching-overload]
                result = _VF.rnn_relu(
                    input,
                    hx,
                    self._flat_weights,  # type: ignore[arg-type]
                    self.bias,
                    self.num_layers,
                    self.dropout,
                    self.training,
                    self.bidirectional,
                    self.batch_first,
                )
        else:
            if self.mode == "RNN_TANH":
                # pyrefly: ignore [no-matching-overload]
                result = _VF.rnn_tanh(
                    input,
                    batch_sizes,
                    hx,
                    self._flat_weights,  # type: ignore[arg-type]
                    self.bias,
                    self.num_layers,
                    self.dropout,
                    self.training,
                    self.bidirectional,
                )
            else:
                # pyrefly: ignore [no-matching-overload]
                result = _VF.rnn_relu(
                    input,
                    batch_sizes,
                    hx,
                    self._flat_weights,  # type: ignore[arg-type]
                    self.bias,
                    self.num_layers,
                    self.dropout,
                    self.training,
                    self.bidirectional,
                )

        output = result[0]
        hidden = result[1]

        if isinstance(orig_input, PackedSequence):
            output_packed = PackedSequence(
                output,
                batch_sizes,
                sorted_indices,
                unsorted_indices,
            )
            return output_packed, self.permute_hidden(hidden, unsorted_indices)

        if not is_batched:  # type: ignore[possibly-undefined]
            output = output.squeeze(batch_dim)  # type: ignore[possibly-undefined]
            hidden = hidden.squeeze(1)

        return output, self.permute_hidden(hidden, unsorted_indices)