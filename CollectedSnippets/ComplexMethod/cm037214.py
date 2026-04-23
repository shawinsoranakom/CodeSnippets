def _prepare_decode_tensors(
        self,
        seq_lens: torch.Tensor,
        block_table: torch.Tensor,
        decode_lens: torch.Tensor,
        decode_lens_cpu: torch.Tensor,
        query_start_loc: torch.Tensor,
        num_decodes: int,
        num_decode_tokens: int,
        use_native: bool,
        next_n: int,
        max_decode_len: int,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int, bool]:
        """Expand seq_lens/block_table/decode_lens for the decode kernels.

        Flatten path (not use_native, max_decode_len > 1):
          Each multi-token decode request is expanded into individual
          single-token entries so the kernel always sees next_n=1.

        Native path (use_native or max_decode_len == 1):
          Plain decode or spec-decode with 2D per-token context lengths.

        Returns (seq_lens, block_table, decode_lens, batch_size, requires_padding).
        seq_lens is 1D (batch_size,) for flatten/plain, 2D (B, next_n) for native MTP.
        """
        min_decode_len = int(decode_lens_cpu.min().item())
        if not use_native and max_decode_len > 1:
            assert self.decode_seq_lens_buffer.dim() == 1
            if min_decode_len == max_decode_len:
                # Uniform decode lengths.
                num_decode_tokens = num_decodes * max_decode_len
                _prepare_uniform_decode_kernel[(num_decode_tokens,)](
                    seq_lens,
                    self.decode_seq_lens_buffer,
                    block_table,
                    block_table.stride(0),
                    self.expanded_block_table_buffer,
                    self.expanded_block_table_buffer.stride(0),
                    self.decode_lens_buffer,
                    max_decode_len,
                    BLOCK_SIZE=1024,
                )
                self.decode_seq_lens_buffer[num_decode_tokens:] = 0
                seq_lens = self.decode_seq_lens_buffer[:num_decode_tokens]
                block_table = self.expanded_block_table_buffer[:num_decode_tokens]
                decode_lens = self.decode_lens_buffer[:num_decode_tokens]
                return seq_lens, block_table, decode_lens, num_decode_tokens, False
            else:
                # Variable decode lengths.
                # Assume 4 requests with seq_lens [10, 7, 12, 0] (the final req is
                # padding) and decode_lens [3, 1, 4, 0] in the below example comments.
                # The context lengths are therefore
                # [10-3, 7-1, 12-4, 0-0] = [7, 6, 8, 0].

                # 3 + 1 + 4 + 0 = 8
                actual_expanded = int(decode_lens_cpu.sum().item())

                # Fuse expanded_base and expanded_starts into a single
                # repeat_interleave:
                # seq_len_i = (context_start[b] - query_start_loc[b]) + arange[i] + 1
                # where context_start[b] = seq_lens[b] - decode_lens[b].
                # Example: offsets = [7-0, 6-3, 8-4, 0-8] = [7, 3, 4, -8]
                # expanded_offsets  = [7, 7, 7, 3, 4, 4, 4, 4]
                # result            = [8, 9, 10, 7, 9, 10, 11, 12]
                expanded_offsets = torch.repeat_interleave(
                    seq_lens - decode_lens - query_start_loc,
                    decode_lens,
                    output_size=actual_expanded,
                )

                # [8, 9, 10, 7, 9, 10, 11, 12, ...] where ... is unused buffer space
                self.decode_seq_lens_buffer[:actual_expanded] = (
                    expanded_offsets + self.arange_buffer[:actual_expanded] + 1
                )
                self.decode_seq_lens_buffer[actual_expanded:] = 0
                seq_lens = self.decode_seq_lens_buffer[:num_decode_tokens]

                # Give each of the flattened entries the same block table row as the
                # original request.
                self.expanded_block_table_buffer[:actual_expanded] = (
                    torch.repeat_interleave(
                        block_table, decode_lens, dim=0, output_size=actual_expanded
                    )
                )
                if actual_expanded < num_decode_tokens:
                    self.expanded_block_table_buffer[
                        actual_expanded:num_decode_tokens, 0
                    ] = 0
                block_table = self.expanded_block_table_buffer[:num_decode_tokens]

                # All reqs now have decode_len=1
                self.decode_lens_buffer[:num_decode_tokens] = 1
                decode_lens = self.decode_lens_buffer[:num_decode_tokens]
                return seq_lens, block_table, decode_lens, num_decode_tokens, False
        else:
            # Native path: plain decode (next_n==1) or spec decode
            # with 2D per-token context lengths (next_n > 1).
            #
            # When decode_lens are not truly uniform (e.g. some requests have
            # decode_len < next_n due to padding or short prefills), the simple
            # reshape in sparse_attn_indexer won't work. Use pack_seq_triton
            # (requires_padding) instead.
            requires_padding = min_decode_len != max_decode_len
            if use_native and next_n > 1:
                assert self.decode_seq_lens_buffer.dim() == 2
                # (B, next_n): token j attends to L - next_n + j + 1 KV tokens
                self.decode_seq_lens_buffer[:num_decodes] = (
                    seq_lens.unsqueeze(1) - next_n + 1 + self.offsets_buffer
                )
                seq_lens = self.decode_seq_lens_buffer[:num_decodes]
            return seq_lens, block_table, decode_lens, num_decodes, requires_padding