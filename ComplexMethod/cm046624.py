def _gguf_skip_value(f, vtype: int) -> None:
        """Skip a GGUF KV value without reading it."""
        sz = LlamaCppBackend._GGUF_TYPE_SIZE.get(vtype)
        if sz is not None:
            f.seek(sz, 1)
        elif vtype == 8:  # STRING
            slen = struct.unpack("<Q", f.read(8))[0]
            f.seek(slen, 1)
        elif vtype == 9:  # ARRAY
            atype = struct.unpack("<I", f.read(4))[0]
            alen = struct.unpack("<Q", f.read(8))[0]
            elem_sz = LlamaCppBackend._GGUF_TYPE_SIZE.get(atype)
            if elem_sz is not None:
                f.seek(elem_sz * alen, 1)
            elif atype == 8:
                for _ in range(alen):
                    slen = struct.unpack("<Q", f.read(8))[0]
                    f.seek(slen, 1)
            else:
                for _ in range(alen):
                    LlamaCppBackend._gguf_skip_value(f, atype)