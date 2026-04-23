def run_up(self, idx, sample_ref, ended, timestep_shift_scale, scaled_timestep, checkpoint_fn, output_buffer, output_offset, max_chunk_size):
        sample = sample_ref[0]
        sample_ref[0] = None
        if idx >= len(self.up_blocks):
            sample = self.conv_norm_out(sample)
            if timestep_shift_scale is not None:
                shift, scale = timestep_shift_scale
                sample = sample * (1 + scale) + shift
            sample = self.conv_act(sample)
            if ended:
                mark_conv3d_ended(self.conv_out)
            sample = self.conv_out(sample, causal=self.causal)
            if sample is not None and sample.shape[2] > 0:
                sample = unpatchify(sample, patch_size_hw=self.patch_size, patch_size_t=1)
                t = sample.shape[2]
                output_buffer[:, :, output_offset[0]:output_offset[0] + t].copy_(sample)
                output_offset[0] += t
            return

        up_block = self.up_blocks[idx]
        if ended:
            mark_conv3d_ended(up_block)
        if self.timestep_conditioning and isinstance(up_block, UNetMidBlock3D):
            sample = checkpoint_fn(up_block)(
                sample, causal=self.causal, timestep=scaled_timestep
            )
        else:
            sample = checkpoint_fn(up_block)(sample, causal=self.causal)

        if sample is None or sample.shape[2] == 0:
            return

        total_bytes = sample.numel() * sample.element_size()
        num_chunks = (total_bytes + max_chunk_size - 1) // max_chunk_size

        if num_chunks == 1:
            # when we are not chunking, detach our x so the callee can free it as soon as they are done
            next_sample_ref = [sample]
            del sample
            self.run_up(idx + 1, next_sample_ref, ended, timestep_shift_scale, scaled_timestep, checkpoint_fn, output_buffer, output_offset, max_chunk_size)
            return
        else:
            samples = torch.chunk(sample, chunks=num_chunks, dim=2)

            for chunk_idx, sample1 in enumerate(samples):
                self.run_up(idx + 1, [sample1], ended and chunk_idx == len(samples) - 1, timestep_shift_scale, scaled_timestep, checkpoint_fn, output_buffer, output_offset, max_chunk_size)