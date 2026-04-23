def fe_supports_quant_scheme(self) -> bool:
        """Check if the fused experts class supports this quant config.
        See https://github.com/ROCm/aiter/issues/2419 for AITER gaps."""
        if self.quant_config is None or self.quant_dtype is None:
            return True
        if self.quant_dtype != torch.float8_e4m3fn:
            return True
        # Derive QuantKeys from test config
        if self.quant_block_shape is not None:
            w_key = kFp8Static128BlockSym
            a_key = kFp8Dynamic128Sym
        elif self.is_per_out_ch_quant:
            w_key = kFp8StaticChannelSym
            a_key = (
                kFp8DynamicTokenSym
                if self.is_per_act_token_quant
                else kFp8StaticTensorSym
            )
        else:
            w_key = kFp8StaticTensorSym
            a_key = (
                kFp8DynamicTensorSym
                if self.is_per_act_token_quant
                else kFp8StaticTensorSym
            )
        fe_cls = self.fused_experts_type
        if hasattr(fe_cls, "_supports_quant_scheme"):
            try:
                return fe_cls._supports_quant_scheme(w_key, a_key)
            except NotImplementedError:
                pass
        return True