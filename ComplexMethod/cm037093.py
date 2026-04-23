def forward(self, x, seq_len, linear_spec=False):
        if x.shape[1] < self.sample_rate * self.pad_min_duration:
            pad_amount = int(self.sample_rate * self.pad_min_duration) - x.shape[1]
            if self.pad_direction == "right":
                x = F.pad(x, (0, pad_amount), value=self.pad_value)
            elif self.pad_direction == "left":
                x = F.pad(x, (pad_amount, 0), value=self.pad_value)
            elif self.pad_direction == "both":
                left_pad = pad_amount // 2
                right_pad = pad_amount - left_pad
                x = F.pad(x, (left_pad, right_pad), value=self.pad_value)
            else:
                raise ValueError(
                    f"{self} received an invalid pad_direction: {self.pad_direction}. "
                    f"It must be one of 'left', 'right', or 'both'."
                )
            seq_len = torch.tensor([x.shape[1]], dtype=torch.float, device=x.device)

        seq_len_time = seq_len
        seq_len_unfixed = self.get_seq_len(seq_len)

        # fix for seq_len = 0 for streaming; if size was 0, it is always padded
        # to 1, and normalizer fails
        seq_len = torch.where(
            seq_len == 0, torch.zeros_like(seq_len_unfixed), seq_len_unfixed
        )

        if self.stft_pad_amount is not None:
            x = torch.nn.functional.pad(
                x.unsqueeze(1), (self.stft_pad_amount, self.stft_pad_amount), "constant"
            ).squeeze(1)

        # use dither for inference as well
        if self.dither > 0:
            x += self.dither * torch.randn(
                x.shape, dtype=x.dtype, device=x.device, generator=self.generator
            )

        # do preemphasis
        if self.preemph is not None:
            timemask = torch.arange(x.shape[1], device=x.device).unsqueeze(
                0
            ) < seq_len_time.unsqueeze(1)
            x = torch.cat(
                (x[:, 0].unsqueeze(1), x[:, 1:] - self.preemph * x[:, :-1]), dim=1
            )

            x = x.masked_fill(~timemask, 0.0)

        x = self.stft(x)

        # torch stft returns complex tensor (of shape [B,N,T]); so convert to magnitude
        # guard is needed for sqrt if grads are passed through
        guard = 0 if not self.use_grads else CONSTANT
        x = torch.view_as_real(x)
        x = torch.sqrt(x.pow(2).sum(-1) + guard)

        # get power spectrum
        if self.mag_power != 1.0:
            x = x.pow(self.mag_power)

        # return plain spectrogram if required
        if linear_spec:
            return x, seq_len

        # disable autocast, otherwise it might be automatically casted to fp16
        # on fp16 compatible GPUs and get NaN values for input value of 65520
        with torch.amp.autocast(x.device.type, enabled=False):
            # dot with filterbank energies
            x = torch.matmul(self.fb.to(x.dtype), x)

        # log features if required
        if self.log:
            if self.log_zero_guard_type == "add":
                x = torch.log(x + self.log_zero_guard_value_fn(x))
            elif self.log_zero_guard_type == "clamp":
                x = torch.log(torch.clamp(x, min=self.log_zero_guard_value_fn(x)))
            else:
                raise ValueError("log_zero_guard_type was not understood")

        # frame splicing if required
        if self.frame_splicing > 1:
            x = self.splice_frames(x, self.frame_splicing)

        # normalize if required
        if self.normalize:
            x, _, _ = self.normalize_batch(x, seq_len, normalize_type=self.normalize)

        # mask to zero any values beyond seq_len in batch, pad to multiple of
        # `pad_to` (for efficiency)
        max_len = x.size(-1)
        mask = torch.arange(max_len, device=x.device)
        mask = mask.repeat(x.size(0), 1) >= seq_len.unsqueeze(1)
        x = x.masked_fill(
            mask.unsqueeze(1).type(torch.bool).to(device=x.device), self.pad_value
        )

        del mask
        pad_to = self.pad_to
        if pad_to == "max":
            x = nn.functional.pad(
                x, (0, self.max_length - x.size(-1)), value=self.pad_value
            )
        elif pad_to > 0:
            pad_amt = x.size(-1) % pad_to
            if pad_amt != 0:
                x = nn.functional.pad(x, (0, pad_to - pad_amt), value=self.pad_value)

        return x, seq_len