def forward(self, input, hx=None):
        self._update_flat_weights()

        orig_input = input
        # xxx: isinstance check needs to be in conditional for TorchScript to compile
        batch_sizes = None
        num_directions = 2 if self.bidirectional else 1
        real_hidden_size = self.proj_size if self.proj_size > 0 else self.hidden_size
        if isinstance(orig_input, PackedSequence):
            input, batch_sizes, sorted_indices, unsorted_indices = input
            max_batch_size = batch_sizes[0]
            if hx is None:
                h_zeros = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    real_hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
                c_zeros = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    self.hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
                hx = (h_zeros, c_zeros)
            else:
                # Each batch of the hidden state should match the input sequence that
                # the user believes he/she is passing in.
                hx = self.permute_hidden(hx, sorted_indices)
        else:
            if input.dim() not in (2, 3):
                raise ValueError(
                    f"LSTM: Expected input to be 2D or 3D, got {input.dim()}D instead"
                )
            is_batched = input.dim() == 3
            batch_dim = 0 if self.batch_first else 1
            if not is_batched:
                input = input.unsqueeze(batch_dim)
            max_batch_size = input.size(0) if self.batch_first else input.size(1)
            sorted_indices = None
            unsorted_indices = None
            if hx is None:
                h_zeros = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    real_hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
                c_zeros = torch.zeros(
                    self.num_layers * num_directions,
                    max_batch_size,
                    self.hidden_size,
                    dtype=input.dtype,
                    device=input.device,
                )
                hx = (h_zeros, c_zeros)
                self.check_forward_args(input, hx, batch_sizes)
            else:
                if is_batched:
                    if hx[0].dim() != 3 or hx[1].dim() != 3:
                        msg = (
                            "For batched 3-D input, hx and cx should "
                            f"also be 3-D but got ({hx[0].dim()}-D, {hx[1].dim()}-D) tensors"
                        )
                        raise RuntimeError(msg)
                else:
                    if hx[0].dim() != 2 or hx[1].dim() != 2:
                        msg = (
                            "For unbatched 2-D input, hx and cx should "
                            f"also be 2-D but got ({hx[0].dim()}-D, {hx[1].dim()}-D) tensors"
                        )
                        raise RuntimeError(msg)
                    hx = (hx[0].unsqueeze(1), hx[1].unsqueeze(1))
                # Each batch of the hidden state should match the input sequence that
                # the user believes he/she is passing in.
                self.check_forward_args(input, hx, batch_sizes)
                hx = self.permute_hidden(hx, sorted_indices)

        if batch_sizes is None:
            # pyrefly: ignore [no-matching-overload]
            result = _VF.lstm(
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
            result = _VF.lstm(
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
        hidden = result[1:]
        # xxx: isinstance check needs to be in conditional for TorchScript to compile
        if isinstance(orig_input, PackedSequence):
            output_packed = PackedSequence(
                output,
                batch_sizes,
                sorted_indices,
                unsorted_indices,
            )
            return output_packed, self.permute_hidden(hidden, unsorted_indices)
        else:
            if not is_batched:  # type: ignore[possibly-undefined]
                output = output.squeeze(batch_dim)  # type: ignore[possibly-undefined]
                hidden = (hidden[0].squeeze(1), hidden[1].squeeze(1))
            return output, self.permute_hidden(hidden, unsorted_indices)