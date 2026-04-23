def checkEmbeddingSerialization(
        self,
        qemb,
        num_embeddings,
        embedding_dim,
        indices,
        offsets,
        set_qconfig,
        is_emb_bag,
        dtype=torch.quint8,
    ):
        # Test serialization of dynamic EmbeddingBag module using state_dict
        if is_emb_bag:
            inputs = [indices, offsets]
        else:
            inputs = [indices]
        emb_dict = qemb.state_dict()
        b = io.BytesIO()
        torch.save(emb_dict, b)
        b.seek(0)
        loaded_dict = torch.load(b)
        embedding_unpack = torch.ops.quantized.embedding_bag_unpack
        # Check unpacked weight values explicitly
        for key in emb_dict:
            if isinstance(emb_dict[key], torch._C.ScriptObject):
                if not isinstance(loaded_dict[key], torch._C.ScriptObject):
                    raise AssertionError(f"Expected loaded_dict[{key!r}] to be ScriptObject")
                emb_weight = embedding_unpack(emb_dict[key])
                loaded_weight = embedding_unpack(loaded_dict[key])
                self.assertEqual(emb_weight, loaded_weight)

        # Check state dict serialization and torch.save APIs
        if is_emb_bag:
            loaded_qemb = nnq.EmbeddingBag(
                num_embeddings=num_embeddings,
                embedding_dim=embedding_dim,
                include_last_offset=True,
                mode="sum",
                dtype=dtype,
            )
        else:
            loaded_qemb = nnq.Embedding(
                num_embeddings=num_embeddings, embedding_dim=embedding_dim, dtype=dtype
            )
        self.check_eager_serialization(qemb, loaded_qemb, inputs)

        loaded_qemb.load_state_dict(loaded_dict)
        self.assertEqual(
            embedding_unpack(qemb._packed_params._packed_weight),
            embedding_unpack(loaded_qemb._packed_params._packed_weight),
        )

        # Test JIT serialization
        self.checkScriptable(qemb, [inputs], check_save_load=True)

        # Test from_float call
        if is_emb_bag:
            float_embedding = torch.nn.EmbeddingBag(
                num_embeddings=num_embeddings,
                embedding_dim=embedding_dim,
                include_last_offset=True,
                scale_grad_by_freq=False,
                mode="sum",
            )
        else:
            float_embedding = torch.nn.Embedding(
                num_embeddings=num_embeddings, embedding_dim=embedding_dim
            )

        if set_qconfig:
            float_qparams_observer = PerChannelMinMaxObserver.with_args(
                dtype=dtype, qscheme=torch.per_channel_affine_float_qparams, ch_axis=0
            )
            float_embedding.qconfig = QConfig(
                activation=default_dynamic_quant_observer, weight=float_qparams_observer
            )

        prepare_dynamic(float_embedding)

        float_embedding(*inputs)
        if is_emb_bag:
            q_embeddingbag = nnq.EmbeddingBag.from_float(float_embedding)
            expected_name = "QuantizedEmbeddingBag"
        else:
            q_embeddingbag = nnq.Embedding.from_float(float_embedding)
            expected_name = "QuantizedEmbedding"

        q_embeddingbag(*inputs)

        self.assertTrue(expected_name in str(q_embeddingbag))