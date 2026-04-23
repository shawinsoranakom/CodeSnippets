def forward_orig(self, sample: torch.FloatTensor, device=None) -> torch.FloatTensor:
        r"""The forward method of the `Encoder` class."""

        max_chunk_size = get_max_chunk_size(sample.device if device is None else device) * 2  # encoder is more memory-efficient than decoder
        frame_size = sample[:, :, :1, :, :].numel() * sample.element_size()
        frame_size = int(frame_size * (self.conv_in.out_channels / self.conv_in.in_channels))

        outputs = []
        samples = [sample[:, :, :1, :, :]]
        if sample.shape[2] > 1:
            chunk_t = max(2, max_chunk_size // frame_size)
            if chunk_t < 4:
                chunk_t = 2
            elif chunk_t < 8:
                chunk_t = 4
            else:
                chunk_t = (chunk_t // 8) * 8
            samples += list(torch.split(sample[:, :, 1:, :, :], chunk_t, dim=2))
        for chunk_idx, chunk in enumerate(samples):
            if chunk_idx == len(samples) - 1:
                mark_conv3d_ended(self)
            chunk = patchify(chunk, patch_size_hw=self.patch_size, patch_size_t=1).to(device=device)
            output = self._forward_chunk(chunk)
            if output is not None:
                outputs.append(output)

        return torch_cat_if_needed(outputs, dim=2)