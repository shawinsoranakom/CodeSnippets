def embedding_bag_rowwise_offsets_run(
            self, bit_rate, num_embeddings,
            embedding_dim, num_offsets,
            use_32bit_indices, use_32bit_offsets,
            enable_per_sample_weights,
            include_last_offset, fallback_to_no_sparse, sparsity, atol, rtol):
        pt_op = torch.ops.quantized.embedding_bag_byte_rowwise_offsets
        pt_prepack_op = torch.ops.quantized.embedding_bag_byte_prepack
        if bit_rate == 4:
            pt_op = torch.ops.quantized.embedding_bag_4bit_rowwise_offsets
            pt_prepack_op = torch.ops.quantized.embedding_bag_4bit_prepack
        elif bit_rate == 2:
            pt_op = torch.ops.quantized.embedding_bag_2bit_rowwise_offsets
            pt_prepack_op = torch.ops.quantized.embedding_bag_2bit_prepack

        weights = torch.from_numpy((np.random.random_sample((
            num_embeddings, embedding_dim)) + 1).astype(np.float32))

        max_segments = 5
        max_segment_length = 20
        num_lengths = np.random.randint(1, max_segments + 1)
        lengths = np.random.randint(0, max_segment_length + 1,
                                    size=num_lengths).astype(np.int32)
        num_indices = np.sum(lengths)

        def lengths_to_offsets(t, offset_type=np.int64, use_begin_offset=True):
            """
            Convert lengths to offsets
            """
            tt = np.zeros((t.shape[0] + 1,), dtype=offset_type)
            tt[1:] = t
            tt = torch.from_numpy(np.cumsum(tt, dtype=offset_type))
            if use_begin_offset:
                return tt[:-1]
            return tt[1:]

        offsets = lengths_to_offsets(lengths)
        indices = torch.from_numpy(np.random.randint(
            low=0, high=num_embeddings, size=num_indices, dtype=np.int64))

        q_weights = pt_prepack_op(weights)
        per_sample_weights = torch.from_numpy(np.random.uniform(
            low=0.01, high=0.5, size=[len(indices)]).astype(np.float32)) if \
            enable_per_sample_weights else None
        if include_last_offset:
            offsets = torch.cat(
                (offsets, torch.tensor([indices.size(0)], dtype=torch.long)), 0
            )

        # Reference result will be the floating point torch.nn.EmbeddingBag.
        def get_reference_result(
                num_embeddings, embedding_dim,
                include_last_offset, weights, per_sample_weights,
                indices, offsets):
            embedding_bag = torch.nn.EmbeddingBag(
                num_embeddings=num_embeddings,
                embedding_dim=embedding_dim,
                include_last_offset=include_last_offset, _weight=weights,
                scale_grad_by_freq=False, mode='sum'
            )
            return embedding_bag(indices, offsets,
                                 per_sample_weights=per_sample_weights)

        mapping_table = np.zeros(num_embeddings, dtype=np.int32)
        pruned_weights = weights
        prune_weights = sparsity > 0
        if prune_weights:
            if fallback_to_no_sparse:
                # Testing that prune_weight with mapping_table {0} will
                # fallback to non sparse embedding look up kernel.
                mapping_table = np.zeros(1, dtype=np.int32)
            else:
                # Prune and generate mapping table
                num_compressed_rows = 0
                unpruned_ids = []
                for i in range(num_embeddings):
                    if np.random.uniform() < sparsity:
                        mapping_table[i] = -1
                        q_weights[i, :] = 0
                        weights[i, :] = 0
                    else:
                        mapping_table[i] = num_compressed_rows
                        num_compressed_rows += 1
                        unpruned_ids.append(i)
                q_weights = q_weights[unpruned_ids]
                pruned_weights = weights[unpruned_ids]

        result = pt_op(q_weights,
                       indices.int() if use_32bit_indices else indices,
                       offsets.int() if use_32bit_offsets else offsets,
                       mode=0,
                       pruned_weights=prune_weights,
                       per_sample_weights=per_sample_weights,
                       compressed_indices_mapping=torch.tensor(mapping_table),
                       include_last_offset=include_last_offset)

        reference_result = get_reference_result(
            num_embeddings, embedding_dim, include_last_offset, weights,
            per_sample_weights, indices, offsets)

        torch.testing.assert_close(reference_result, result, atol=atol, rtol=rtol)


        if bit_rate == 8 or bit_rate == 4:
            # Test operator that accepts TorchBind packed weights.
            if bit_rate == 4:
                qdtype = torch.quint4x2
                op = torch.ops.quantized.embedding_bag_4bit
            else:
                qdtype = torch.quint8
                op = torch.ops.quantized.embedding_bag_byte
            obs = PerChannelMinMaxObserver(dtype=qdtype, qscheme=torch.per_channel_affine_float_qparams, ch_axis=0)
            obs(pruned_weights)
            # Get the scale and zero point for the weight tensor
            qparams = obs.calculate_qparams()
            # Quantize the weights to 8bits
            qweight = torch.quantize_per_channel(pruned_weights, qparams[0], qparams[1], axis=0, dtype=qdtype)
            packed_weight = torch.ops.quantized.embedding_bag_prepack(qweight)
            result = op(packed_weight, indices, offsets, mode=0,
                        pruned_weights=prune_weights,
                        per_sample_weights=per_sample_weights,
                        compressed_indices_mapping=torch.tensor(mapping_table),
                        include_last_offset=include_last_offset)
            torch.testing.assert_close(reference_result, result, atol=atol, rtol=rtol)