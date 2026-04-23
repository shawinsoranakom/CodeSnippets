def _dtypes(self, kind):
        bool = torch.bool
        int8 = torch.int8
        int16 = torch.int16
        int32 = torch.int32
        int64 = torch.int64
        uint8 = torch.uint8
        # uint16, uint32, and uint64 are present in newer versions of pytorch,
        # but they aren't generally supported by the array API functions, so
        # we omit them from this function.
        float32 = torch.float32
        float64 = torch.float64
        complex64 = torch.complex64
        complex128 = torch.complex128

        if kind is None:
            return {
                "bool": bool,
                "int8": int8,
                "int16": int16,
                "int32": int32,
                "int64": int64,
                "uint8": uint8,
                "float32": float32,
                "float64": float64,
                "complex64": complex64,
                "complex128": complex128,
            }
        if kind == "bool":
            return {"bool": bool}
        if kind == "signed integer":
            return {
                "int8": int8,
                "int16": int16,
                "int32": int32,
                "int64": int64,
            }
        if kind == "unsigned integer":
            return {
                "uint8": uint8,
            }
        if kind == "integral":
            return {
                "int8": int8,
                "int16": int16,
                "int32": int32,
                "int64": int64,
                "uint8": uint8,
            }
        if kind == "real floating":
            return {
                "float32": float32,
                "float64": float64,
            }
        if kind == "complex floating":
            return {
                "complex64": complex64,
                "complex128": complex128,
            }
        if kind == "numeric":
            return {
                "int8": int8,
                "int16": int16,
                "int32": int32,
                "int64": int64,
                "uint8": uint8,
                "float32": float32,
                "float64": float64,
                "complex64": complex64,
                "complex128": complex128,
            }
        if isinstance(kind, tuple):
            res = {}
            for k in kind:
                res.update(self.dtypes(kind=k))
            return res
        raise ValueError(f"unsupported kind: {kind!r}")