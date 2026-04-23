def frexp(x):
        cache_keys = f"frexp({x})[0]", f"frexp({x})[1]"
        if all(V.kernel.cse.try_get(cache_key) is not None for cache_key in cache_keys):
            return tuple(V.kernel.cse.try_get(cache_key) for cache_key in cache_keys)

        cdtype = DTYPE_TO_CPP[x.dtype]
        size = V.kernel.tail_size if V.kernel.tail_size else V.kernel.tiling_factor
        code = BracesBuffer()
        exponent = V.kernel.cse.newvar(dtype=torch.int32)
        mantissa = V.kernel.cse.newvar(dtype=x.dtype)
        exponent.update_on_args("frexp", (x,), kwargs={})
        mantissa.update_on_args("frexp", (x,), kwargs={})
        n_vec = V.kernel._get_num_vectors(x.dtype)
        mantissa_t = (
            f"at::vec::Vectorized<{cdtype}>"
            if n_vec == 1
            else f"at::vec::VectorizedN<{cdtype}, {n_vec}>"
        )
        code.writeline(
            f"at::vec::Vectorized<int32_t> {exponent};"
            if n_vec == 1
            else f"at::vec::VectorizedN<int32_t, {n_vec}> {exponent};"
        )
        code.writeline(f"{mantissa_t} {mantissa};")
        code.writeline("[&]()")
        with code.indent():
            code.writeline(
                f"__at_align__ std::array<{cdtype}, {V.kernel.tiling_factor}> tmpbuf;"
            )
            code.writeline(f"{x}.store(tmpbuf.data(), {cexpr_index(size)});")
            code.writeline(
                f"__at_align__ std::array<int32_t, {V.kernel.tiling_factor}> tmpbuf_exponent;"
            )
            code.writeline(
                f"__at_align__ std::array<{cdtype}, {V.kernel.tiling_factor}> tmpbuf_mantissa;"
            )
            code.writeline(f"for (int i = 0; i < {cexpr_index(size)}; i++)")
            with code.indent():
                code.writeline(
                    "tmpbuf_mantissa[i] = std::frexp(tmpbuf[i], &tmpbuf_exponent[i]);"
                )
            code.writeline(
                f"{exponent} = at::vec::Vectorized<int32_t>::loadu(tmpbuf_exponent.data(), {cexpr_index(size)});"
                if n_vec == 1
                else f"{exponent} = at::vec::VectorizedN<int32_t, {n_vec}>::loadu(tmpbuf_exponent.data(), {cexpr_index(size)});"
            )
            code.writeline(
                f"{mantissa} = {mantissa_t}::loadu(tmpbuf_mantissa.data(), {cexpr_index(size)});"
            )
        code.writeline("();")
        V.kernel.compute.splice(code)
        cse_vars = (mantissa, exponent)
        for cache_key, cse_var in zip(cache_keys, cse_vars):
            V.kernel.cse.put(cache_key, cse_var)
        return mantissa, exponent