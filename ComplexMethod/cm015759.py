def test_ptq_quantize_first(self):
        """The expectation is post_training_sparse_quantize function
        1. Takes in a model
        2. Quantize the embeddings
        3. Sparsifies the embeddings

        This unit test checks that
        1. Embeddings and EmbeddingBags are sparsified to the right sparsity levels
        2. Embeddings and EmbeddingBags are quantized
        3. Linear modules are not quantized
        """
        model = Model()

        sparse_config = {"sparsity_level": 0.8, "sparse_block_shape": (1, 1)}
        post_training_sparse_quantize(
            model, DataNormSparsifier, sparsify_first=False, **sparse_config
        )

        if (
            type(model.emb1)
            is not torch.ao.nn.quantized.modules.embedding_ops.Embedding
        ):
            raise AssertionError(
                f"Expected quantized Embedding, got {type(model.emb1)}"
            )
        if (
            type(model.embbag1)
            is not torch.ao.nn.quantized.modules.embedding_ops.EmbeddingBag
        ):
            raise AssertionError(
                f"Expected quantized EmbeddingBag, got {type(model.embbag1)}"
            )
        if (
            type(model.emb_seq[0])
            is not torch.ao.nn.quantized.modules.embedding_ops.Embedding
        ):
            raise AssertionError(
                f"Expected quantized Embedding, got {type(model.emb_seq[0])}"
            )
        if (
            type(model.emb_seq[1])
            is not torch.ao.nn.quantized.modules.embedding_ops.EmbeddingBag
        ):
            raise AssertionError(
                f"Expected quantized EmbeddingBag, got {type(model.emb_seq[1])}"
            )
        if type(model.linear1) is not nn.Linear:
            raise AssertionError(
                f"Expected nn.Linear (not quantized), got {type(model.linear1)}"
            )
        if type(model.linear2) is not nn.Linear:
            raise AssertionError(
                f"Expected nn.Linear (not quantized), got {type(model.linear2)}"
            )

        dequant_emb1 = torch.dequantize(model.emb1.weight())
        dequant_embbag1 = torch.dequantize(model.embbag1.weight())
        dequant_emb_seq_0 = torch.dequantize(model.emb_seq[0].weight())
        dequant_emb_seq_1 = torch.dequantize(model.emb_seq[1].weight())

        # higher threshold as quantization occurs before sparsity
        threshold = (
            1  # zero points seem to have higher magnitude with sparsity occurring after
        )

        sl_emb1 = (torch.abs(dequant_emb1) < threshold).float().mean()
        sl_embbag1 = (torch.abs(dequant_embbag1) < threshold).float().mean()
        sl_emb_seq_0 = (torch.abs(dequant_emb_seq_0) < threshold).float().mean()
        sl_emb_seq_1 = (torch.abs(dequant_emb_seq_1) < threshold).float().mean()

        if abs(sl_emb1 - 0.80) > 0.05:
            raise AssertionError(f"Expected sl_emb1 ~0.80, got {sl_emb1}")
        if abs(sl_embbag1 - 0.80) > 0.05:
            raise AssertionError(f"Expected sl_embbag1 ~0.80, got {sl_embbag1}")
        if abs(sl_emb_seq_0 - 0.80) > 0.05:
            raise AssertionError(f"Expected sl_emb_seq_0 ~0.80, got {sl_emb_seq_0}")
        if abs(sl_emb_seq_1 - 0.80) > 0.05:
            raise AssertionError(f"Expected sl_emb_seq_1 ~0.80, got {sl_emb_seq_1}")