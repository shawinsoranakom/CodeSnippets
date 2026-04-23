def calc_updown(self, orig_weight):
        oft_blocks = self.oft_blocks.to(orig_weight.device)
        eye = torch.eye(self.block_size, device=oft_blocks.device)

        if not self.is_R:
            block_Q = oft_blocks - oft_blocks.transpose(-1, -2) # ensure skew-symmetric orthogonal matrix
            if self.constraint != 0:
                norm_Q = torch.norm(block_Q.flatten())
                new_norm_Q = torch.clamp(norm_Q, max=self.constraint.to(oft_blocks.device))
                block_Q = block_Q * ((new_norm_Q + 1e-8) / (norm_Q + 1e-8))
            oft_blocks = torch.matmul(eye + block_Q, (eye - block_Q).float().inverse())

        R = oft_blocks.to(orig_weight.device)

        if not self.is_boft:
            # This errors out for MultiheadAttention, might need to be handled up-stream
            merged_weight = rearrange(orig_weight, '(k n) ... -> k n ...', k=self.num_blocks, n=self.block_size)
            merged_weight = torch.einsum(
                'k n m, k n ... -> k m ...',
                R,
                merged_weight
            )
            merged_weight = rearrange(merged_weight, 'k m ... -> (k m) ...')
        else:
            # TODO: determine correct value for scale
            scale = 1.0
            m = self.boft_m
            b = self.boft_b
            r_b = b // 2
            inp = orig_weight
            for i in range(m):
                bi = R[i] # b_num, b_size, b_size
                if i == 0:
                    # Apply multiplier/scale and rescale into first weight
                    bi = bi * scale + (1 - scale) * eye
                inp = rearrange(inp, "(c g k) ... -> (c k g) ...", g=2, k=2**i * r_b)
                inp = rearrange(inp, "(d b) ... -> d b ...", b=b)
                inp = torch.einsum("b i j, b j ... -> b i ...", bi, inp)
                inp = rearrange(inp, "d b ... -> (d b) ...")
                inp = rearrange(inp, "(c k g) ... -> (c g k) ...", g=2, k=2**i * r_b)
            merged_weight = inp

        # Rescale mechanism
        if self.rescale is not None:
            merged_weight = self.rescale.to(merged_weight) * merged_weight

        updown = merged_weight.to(orig_weight.device) - orig_weight.to(merged_weight.dtype)
        output_shape = orig_weight.shape
        return self.finalize_updown(updown, orig_weight, output_shape)
