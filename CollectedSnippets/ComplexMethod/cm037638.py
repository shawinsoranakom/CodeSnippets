def get_quant_method(
        self,
        layer: torch.nn.Module,
        prefix: str,
    ) -> "QuantizeMethodBase | None":
        if isinstance(layer, LinearBase):
            # collect schemes
            quant_scheme = self.get_scheme(layer=layer, layer_name=prefix)
            input_tfms, output_tfms = get_linear_transform_schemes(
                layer, prefix, self.transform_config, self.packed_modules_mapping
            )

            # choose quantization method
            quant_method: LinearMethodBase = UnquantizedLinearMethod()
            if quant_scheme is not None:
                layer.scheme = quant_scheme
                quant_method = CompressedTensorsLinearMethod(self)

            # choose transform method
            if any((input_tfms, output_tfms)):
                return CompressedTensorsLinearTransformMethod.from_schemes(
                    quant_method, quant_scheme, input_tfms, output_tfms
                )

            else:
                return quant_method

        if isinstance(layer, ParallelLMHead):
            try:
                quant_scheme = self.get_scheme(layer=layer, layer_name=prefix)
            except ValueError:
                quant_scheme = None
            if quant_scheme is not None:
                layer.scheme = quant_scheme
                return CompressedTensorsLinearMethod(self)

        if isinstance(layer, Attention):
            return CompressedTensorsKVCacheMethod(self)
        if isinstance(layer, FusedMoE):
            return CompressedTensorsMoEMethod.get_moe_method(
                self, layer, layer_name=prefix
            )
        return None