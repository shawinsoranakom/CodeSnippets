def _build_fi_prefill_wrappers(self, prefill: FlashInferPrefillMetadata):
        qo_indptr = prefill.query_start_loc

        has_context = False
        if prefill.chunked_context is not None:
            chunked_context = prefill.chunked_context
            has_context = True

        if self._fi_prefill_main is None:
            from flashinfer import BatchPrefillWithRaggedKVCacheWrapper

            self._fi_prefill_main = BatchPrefillWithRaggedKVCacheWrapper(
                self._workspace_buffer, "NHD", backend="cutlass"
            )

        if has_context:
            num_chunks = chunked_context.cu_seq_lens.shape[0]
            # Allocate more prefill chunk wrappers if needed
            if len(self._fi_prefill_chunks) < num_chunks:
                from flashinfer import BatchPrefillWithRaggedKVCacheWrapper

                for _ in range(len(self._fi_prefill_chunks), num_chunks):
                    self._fi_prefill_chunks.append(
                        BatchPrefillWithRaggedKVCacheWrapper(
                            self._workspace_buffer, "NHD", backend="cutlass"
                        )
                    )
            assert num_chunks <= len(self._fi_prefill_chunks)

        # In MLA, the non-latent num_qo_heads == num_kv_heads
        num_qo_heads = self.num_heads
        num_kv_heads = num_qo_heads

        # Sanity: Verify that num_kv_heads == 1 since it is latent space
        assert self.kv_cache_spec.num_kv_heads == 1

        # Get non-latent head_dim_qk and head_dim_vo
        head_dim_qk = self.mla_dims.qk_nope_head_dim + self.mla_dims.qk_rope_head_dim
        head_dim_vo = self.mla_dims.v_head_dim

        # For main run, qo_indptr == kv_indptr
        kv_indptr = qo_indptr.clone()

        # Prepare main prefill
        self._fi_prefill_main.plan(
            qo_indptr=qo_indptr,
            kv_indptr=kv_indptr,
            num_qo_heads=num_qo_heads,
            num_kv_heads=num_kv_heads,
            head_dim_qk=head_dim_qk,
            head_dim_vo=head_dim_vo,
            causal=True,  # This is main run
            sm_scale=self._global_hyperparameters.sm_scale,
            window_left=self._global_hyperparameters.window_left,
            logits_soft_cap=self._global_hyperparameters.logits_soft_cap,
            q_data_type=self.q_data_type,
            o_data_type=prefill.output_dtype,
        )

        # Prepare context prefills
        if has_context:
            for i in range(num_chunks):
                kv_indptr_chunk = chunked_context.cu_seq_lens[i]

                self._fi_prefill_chunks[i].plan(
                    qo_indptr=qo_indptr,
                    kv_indptr=kv_indptr_chunk,
                    num_qo_heads=num_qo_heads,
                    num_kv_heads=num_kv_heads,
                    head_dim_qk=head_dim_qk,
                    head_dim_vo=head_dim_vo,
                    causal=False,  # This is context run
                    sm_scale=self._global_hyperparameters.sm_scale,
                    window_left=self._global_hyperparameters.window_left,
                    logits_soft_cap=self._global_hyperparameters.logits_soft_cap,
                    q_data_type=self.q_data_type,
                    o_data_type=prefill.output_dtype,
                )

        prefill.prefill_main = self._fi_prefill_main
        prefill.prefill_chunks = self._fi_prefill_chunks