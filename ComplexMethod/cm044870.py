def forward(self, raw_audio, target=None, return_loss_breakdown=False):
        """
        einops

        b - batch
        f - freq
        t - time
        s - audio channel (1 for mono, 2 for stereo)
        n - number of 'stems'
        c - complex (2)
        d - feature dimension
        """

        device = raw_audio.device

        # defining whether model is loaded on MPS (MacOS GPU accelerator)
        x_is_mps = True if device.type == "mps" else False

        if raw_audio.ndim == 2:
            raw_audio = rearrange(raw_audio, "b t -> b 1 t")

        channels = raw_audio.shape[1]
        assert (not self.stereo and channels == 1) or (self.stereo and channels == 2), (
            "stereo needs to be set to True if passing in audio signal that is stereo (channel dimension of 2). also need to be False if mono (channel dimension of 1)"
        )

        # to stft

        raw_audio, batch_audio_channel_packed_shape = pack_one(raw_audio, "* t")

        stft_window = self.stft_window_fn(device=device)

        # RuntimeError: FFT operations are only supported on MacOS 14+
        # Since it's tedious to define whether we're on correct MacOS version - simple try-catch is used
        try:
            stft_repr = torch.stft(raw_audio, **self.stft_kwargs, window=stft_window, return_complex=True)
        except:
            stft_repr = torch.stft(
                raw_audio.cpu() if x_is_mps else raw_audio,
                **self.stft_kwargs,
                window=stft_window.cpu() if x_is_mps else stft_window,
                return_complex=True,
            ).to(device)

        stft_repr = torch.view_as_real(stft_repr)

        stft_repr = unpack_one(stft_repr, batch_audio_channel_packed_shape, "* f t c")

        # merge stereo / mono into the frequency, with frequency leading dimension, for band splitting
        stft_repr = rearrange(stft_repr, "b s f t c -> b (f s) t c")

        x = rearrange(stft_repr, "b f t c -> b t (f c)")

        if self.use_torch_checkpoint:
            x = checkpoint(self.band_split, x, use_reentrant=False)
        else:
            x = self.band_split(x)

        # axial / hierarchical attention

        store = [None] * len(self.layers)
        for i, transformer_block in enumerate(self.layers):
            if len(transformer_block) == 3:
                linear_transformer, time_transformer, freq_transformer = transformer_block

                x, ft_ps = pack([x], "b * d")
                if self.use_torch_checkpoint:
                    x = checkpoint(linear_transformer, x, use_reentrant=False)
                else:
                    x = linear_transformer(x)
                (x,) = unpack(x, ft_ps, "b * d")
            else:
                time_transformer, freq_transformer = transformer_block

            if self.skip_connection:
                # Sum all previous
                for j in range(i):
                    x = x + store[j]

            x = rearrange(x, "b t f d -> b f t d")
            x, ps = pack([x], "* t d")

            if self.use_torch_checkpoint:
                x = checkpoint(time_transformer, x, use_reentrant=False)
            else:
                x = time_transformer(x)

            (x,) = unpack(x, ps, "* t d")
            x = rearrange(x, "b f t d -> b t f d")
            x, ps = pack([x], "* f d")

            if self.use_torch_checkpoint:
                x = checkpoint(freq_transformer, x, use_reentrant=False)
            else:
                x = freq_transformer(x)

            (x,) = unpack(x, ps, "* f d")

            if self.skip_connection:
                store[i] = x

        x = self.final_norm(x)

        num_stems = len(self.mask_estimators)

        if self.use_torch_checkpoint:
            mask = torch.stack([checkpoint(fn, x, use_reentrant=False) for fn in self.mask_estimators], dim=1)
        else:
            mask = torch.stack([fn(x) for fn in self.mask_estimators], dim=1)
        mask = rearrange(mask, "b n t (f c) -> b n f t c", c=2)

        # modulate frequency representation

        stft_repr = rearrange(stft_repr, "b f t c -> b 1 f t c")

        # complex number multiplication

        stft_repr = torch.view_as_complex(stft_repr)
        mask = torch.view_as_complex(mask)

        stft_repr = stft_repr * mask

        # istft

        stft_repr = rearrange(stft_repr, "b n (f s) t -> (b n s) f t", s=self.audio_channels)

        # same as torch.stft() fix for MacOS MPS above
        try:
            recon_audio = torch.istft(
                stft_repr, **self.stft_kwargs, window=stft_window, return_complex=False, length=raw_audio.shape[-1]
            )
        except:
            recon_audio = torch.istft(
                stft_repr.cpu() if x_is_mps else stft_repr,
                **self.stft_kwargs,
                window=stft_window.cpu() if x_is_mps else stft_window,
                return_complex=False,
                length=raw_audio.shape[-1],
            ).to(device)

        recon_audio = rearrange(recon_audio, "(b n s) t -> b n s t", s=self.audio_channels, n=num_stems)

        if num_stems == 1:
            recon_audio = rearrange(recon_audio, "b 1 s t -> b s t")

        # if a target is passed in, calculate loss for learning

        if not exists(target):
            return recon_audio

        if self.num_stems > 1:
            assert target.ndim == 4 and target.shape[1] == self.num_stems

        if target.ndim == 2:
            target = rearrange(target, "... t -> ... 1 t")

        target = target[..., : recon_audio.shape[-1]]  # protect against lost length on istft

        loss = F.l1_loss(recon_audio, target)

        multi_stft_resolution_loss = 0.0

        for window_size in self.multi_stft_resolutions_window_sizes:
            res_stft_kwargs = dict(
                n_fft=max(window_size, self.multi_stft_n_fft),  # not sure what n_fft is across multi resolution stft
                win_length=window_size,
                return_complex=True,
                window=self.multi_stft_window_fn(window_size, device=device),
                **self.multi_stft_kwargs,
            )

            recon_Y = torch.stft(rearrange(recon_audio, "... s t -> (... s) t"), **res_stft_kwargs)
            target_Y = torch.stft(rearrange(target, "... s t -> (... s) t"), **res_stft_kwargs)

            multi_stft_resolution_loss = multi_stft_resolution_loss + F.l1_loss(recon_Y, target_Y)

        weighted_multi_resolution_loss = multi_stft_resolution_loss * self.multi_stft_resolution_loss_weight

        total_loss = loss + weighted_multi_resolution_loss

        if not return_loss_breakdown:
            return total_loss

        return total_loss, (loss, multi_stft_resolution_loss)