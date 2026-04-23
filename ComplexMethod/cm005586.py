def validate_environment(self, *args, **kwargs):
        if not is_optimum_available():
            raise ImportError("Loading a GPTQ quantized model requires optimum (`pip install optimum`)")

        gptq_supports_cpu = is_gptqmodel_available()
        if not gptq_supports_cpu and not torch.cuda.is_available():
            raise RuntimeError("GPU is required to quantize or run quantize model.")
        elif not is_gptqmodel_available():
            raise ImportError("Loading a GPTQ quantized model requires gptqmodel (`pip install gptqmodel`) library.")
        elif is_gptqmodel_available() and (
            version.parse(metadata.version("gptqmodel")) < version.parse(MIN_GPTQ_VERSION)
            or version.parse(metadata.version("optimum")) < version.parse(MIN_OPTIMUM_VERSION)
        ):
            raise ImportError(
                f"The gptqmodel version should be >= {MIN_GPTQ_VERSION}, optimum version should >= {MIN_OPTIMUM_VERSION}"
            )