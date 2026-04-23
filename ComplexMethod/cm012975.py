def from_float(cls, mod, use_precomputed_fake_quant=False):
        r"""Create a quantized embedding module from a float module

        Args:
            mod (Module): a float module, either produced by torch.ao.quantization
                          utilities or provided by user
        """
        if hasattr(mod, "weight_fake_quant"):
            if type(mod) is not torch.ao.nn.qat.Embedding:
                raise AssertionError(
                    "nnq."
                    + cls.__name__
                    + ".from_float "
                    + "with fake quant only works for "
                    + torch.ao.nn.qat.Embedding.__name__
                )
            weight_observer = mod.weight_fake_quant
        else:
            if type(mod) is not nn.Embedding:
                raise AssertionError(
                    "nnq."
                    + cls.__name__
                    + ".from_float only works for "
                    + nn.Embedding.__name__
                )
            if not hasattr(mod, "qconfig"):
                raise AssertionError(
                    "Embedding input float module must have qconfig defined"
                )
            from torch.ao.quantization import float_qparams_weight_only_qconfig

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
                "Embedding quantization is only supported with float_qparams_weight_only_qconfig."
            )

        if dtype != torch.quint8 and dtype != torch.quint4x2:
            raise AssertionError(
                f"The only supported dtype for nnq.Embedding is torch.quint8 and torch.quint4x2, got {dtype}"
            )

        # Run the observer to calculate qparams.
        weight_observer(mod.weight)
        qweight = _quantize_weight(mod.weight.float(), weight_observer)

        # Create quantized Embedding module and pass in the quantized weight
        qembedding = Embedding(mod.num_embeddings, mod.embedding_dim)
        qembedding.set_weight(qweight)
        return qembedding