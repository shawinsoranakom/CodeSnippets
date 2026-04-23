def from_dict(cls, config_dict, return_unused_kwargs=False, **kwargs):
        quant_method = config_dict["quant_method"]
        if "auto-round" not in quant_method and "gptq" not in quant_method and "awq" not in quant_method:
            raise NotImplementedError(
                "Failed to convert to auto_round format. Only `gptqv1`, `awq`, and `auto-round` formats are supported."
            )

        if "gptq" in quant_method and "meta" in config_dict:
            raise NotImplementedError("Failed to convert gptq format to auto_round format. Only supports `gptqv1`")

        if "awq" in quant_method and config_dict.get("version", "gemm") != "gemm":
            raise NotImplementedError(
                "Failed to convert awq format to auto_round format. Only supports awq format with gemm version"
            )

        if "auto-round" not in quant_method:
            config_dict["packing_format"] = f"auto_round:{quant_method}"

        return super().from_dict(config_dict, return_unused_kwargs=return_unused_kwargs, **kwargs)