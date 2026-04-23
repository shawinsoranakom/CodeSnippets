def _init_candidates(self) -> None:
        """Build priority-ordered candidate lists for each token count."""
        capture_sizes = self.compilation_config.cudagraph_capture_sizes
        if not (self.cudagraph_mode and capture_sizes):
            return

        capture_sizes = sorted(capture_sizes)
        max_decode_tokens = self.max_num_reqs * self.decode_query_len
        decode_mode = self.cudagraph_mode.decode_mode()
        mixed_mode = self.cudagraph_mode.mixed_mode()
        separate_decode_routine = self.cudagraph_mode.separate_routine()

        descs_by_token_count = defaultdict(list)
        descs_by_mode = defaultdict(list)

        for num_tokens in capture_sizes:
            # Capture uniform decode specfifc graphs if required
            #  (i.e. separate decode routine)
            if (
                separate_decode_routine
                and decode_mode
                and self.decode_query_len <= num_tokens <= max_decode_tokens
            ):
                desc = BatchExecutionDescriptor(
                    cg_mode=decode_mode,
                    num_tokens=num_tokens,
                    num_reqs=num_tokens // self.decode_query_len,
                    uniform_token_count=self.decode_query_len,
                )
                descs_by_mode[decode_mode].append(desc)
                descs_by_token_count[num_tokens].append(desc)

            if mixed_mode:
                # for PIECEWISE graphs there is no limit on requests when replaying
                # i.e. no request padding is needed
                # so we leave it as None
                num_reqs = (
                    min(num_tokens, self.max_num_reqs)
                    if mixed_mode == CUDAGraphMode.FULL
                    else None
                )
                desc = BatchExecutionDescriptor(
                    cg_mode=mixed_mode,
                    num_tokens=num_tokens,
                    num_reqs=num_reqs,
                )
                descs_by_mode[mixed_mode].append(desc)
                descs_by_token_count[num_tokens].append(desc)

        if not descs_by_token_count:
            return

        sorted_padded = sorted(descs_by_token_count.keys())
        self._candidates = [[] for _ in range(sorted_padded[-1] + 1)]

        current_range_start = 0
        for cg_size in sorted_padded:
            for i in range(current_range_start, cg_size + 1):
                self._candidates[i] = descs_by_token_count[cg_size]
            current_range_start = cg_size + 1

        for mode, descs in descs_by_mode.items():
            descs.sort(key=lambda d: d.num_tokens, reverse=True)
            self._capture_descs[mode] = descs