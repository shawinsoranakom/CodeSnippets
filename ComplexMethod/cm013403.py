def pickle(cls, op: object, options: Options) -> "_OpPickleData":
        if isinstance(op, str):
            return _OpStrPickleData(op)

        if isinstance(getattr(op, "__wrapped__", None), AOTCompiledArtifact):
            if not hasattr(op, "__wrapped__"):
                raise AssertionError("op missing __wrapped__ attribute")
            artifact = op.__wrapped__
            if not isinstance(artifact, AOTCompiledArtifact):
                raise AssertionError(
                    f"Expected AOTCompiledArtifact, got {type(artifact)}"
                )
            return _OpPrecompiledPickleData(artifact)

        name = torch.fx.Node._pretty_print_target(op)

        if isinstance(op, torch._ops.OpOverload):
            return cls._pickle_op(name, _OpOverloadPickleData, options)
        elif isinstance(op, torch._ops.OpOverloadPacket):
            return cls._pickle_op(name, _OpOverloadPacketPickleData, options)
        elif name.startswith(_OpFunctionPickleData.SUPPORTED_ROOTS):
            root, detail = name.split(".", 1)
            return _OpFunctionPickleData(root, detail)
        else:
            # TODO: raise a BypassFxGraphCache so we will just bypass this one...
            raise NotImplementedError(f"TARGET: {type(op)} {op} {name}")