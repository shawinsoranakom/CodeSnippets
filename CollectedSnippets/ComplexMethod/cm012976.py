def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a quantized embedding_bag module from a float module

        Args:
            mod (Module): a float module, either produced by torch.ao.quantization
                          utilities or provided by user
        """
        if hasattr(mod, "weight_fake_quant"):
            weight_observer = mod.weight_fake_quant
        else:
            if type(mod) is not nn.EmbeddingBag:
                raise AssertionError(
                    "nnq."
                    + cls.__name__
                    + ".from_float only works for "
                    + nn.EmbeddingBag.__name__
                )
            if not hasattr(mod, "qconfig"):
                raise AssertionError(
                    "EmbeddingBag input float module must have qconfig defined"
                )
            from torch.ao.quantization.qconfig import float_qparams_weight_only_qconfig

            if mod.qconfig is not None and mod.qconfig.weight is not None:  # type: ignore[union-attr]
                weight_observer = mod.qconfig.weight()  # type: ignore[union-attr, operator]
            else:
                weight_observer = float_qparams_weight_only_qconfig.weight()

        dtype = weight_observer.dtype
        is_float_qparams_qconfig = (
            weight_observer.qscheme == torch.per_channel_affine_float_qparams
        )
        if not is_float_qparams_qconfig:
            raise AssertionError(
                "EmbeddingBag quantization is only supported with float_qparams_weight_only_qconfig."
            )

        if dtype != torch.quint8 and dtype != torch.quint4x2:
            raise AssertionError(
                f"The only supported dtype for nnq.EmbeddingBag is torch.quint8 and torch.quint4x2, got {dtype}"
            )

        # Run the observer to calculate qparams.
        weight_observer(mod.weight)
        qweight = _quantize_weight(mod.weight.float(), weight_observer)

        # Create quantized EmbeddingBag module and pass in the quantized weight
        qembedding_bag = EmbeddingBag(
            mod.num_embeddings,
            mod.embedding_dim,
            max_norm=mod.max_norm,
            norm_type=mod.norm_type,
            scale_grad_by_freq=mod.scale_grad_by_freq,
            mode=mod.mode,
            sparse=mod.sparse,
            include_last_offset=mod.include_last_offset,
            dtype=dtype,
        )
        qembedding_bag.set_weight(qweight)
        return qembedding_bag