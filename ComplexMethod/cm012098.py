def _codegen_glue(cls, meta: HalideMeta, headerfile: object) -> str:
        is_cuda = meta.is_cuda()
        assert is_cuda is ("user_context" in meta.target)
        assert "no_runtime" in meta.target
        buffers = []
        buffer_names = []
        for i, arg in enumerate(meta.argtypes):
            if arg.is_buffer():
                # pyrefly: ignore [bad-argument-type]
                buffer_names.append(f"&hl_buf_{i}")
                buffers.extend(cls._codegen_buffer(f"hl_buf_{i}", arg, is_cuda))
            else:
                assert "*" not in arg.ctype
                # pyrefly: ignore [bad-argument-type]
                buffer_names.append(arg.name)
        buffers = "\n".join([f"    {line}" for line in buffers]).lstrip()

        glue_template = cls.glue_template_cuda if is_cuda else cls.glue_template_cpp
        glue_code = glue_template.format(
            halideruntime_h=cls.find_header(
                "HalideRuntimeCuda.h" if is_cuda else "HalideRuntime.h"
            ),
            headerfile=headerfile,
            argdefs=", ".join(
                f"{a.bindings_type()} {a.name}"
                for a in meta.argtypes
                if a.alias_of is None
            ),
            buffers=buffers,
            buffer_names=", ".join(buffer_names),
        )
        return glue_code