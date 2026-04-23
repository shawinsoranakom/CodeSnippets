def inner(*args, **kwargs):
            assert not kwargs
            kernel = V.kernel
            assert isinstance(kernel, CppVecKernel)
            code = BracesBuffer()
            code.writeline("[&]()")
            vec_dtype = args[0].dtype
            n_vec = kernel._get_num_vectors(vec_dtype)
            size = kernel.tail_size if kernel.tail_size else kernel.tiling_factor
            scalar_args = []
            cdtype = DTYPE_TO_CPP[vec_dtype]
            output_mask = scalar_func.__name__ in (
                "isinf",
                "isnan",
                "signbit",
            )
            octype = "bool" if output_mask else cdtype
            octype = (
                DTYPE_TO_CPP[args[-2]]
                if (scalar_func.__name__ == "to_dtype_bitcast")
                else octype
            )
            with code.indent():
                for argidx, arg in enumerate(args):
                    if isinstance(arg, CppCSEVariable):
                        assert arg.is_vec
                        assert arg.dtype == vec_dtype
                        code.writeline(
                            f"__at_align__ std::array<{cdtype}, {kernel.tiling_factor}> tmpbuf{argidx};"
                        )
                        code.writeline(
                            f"{arg}.store(tmpbuf{argidx}.data(), {cexpr_index(size)});"
                        )
                        scalar_args.append(f"tmpbuf{argidx}[i]")
                    else:
                        scalar_args.append(arg)
                code.writeline(
                    f"__at_align__ std::array<{octype}, {kernel.tiling_factor}> tmpbuf_out;"
                )
                res = scalar_func(*scalar_args)
                code.writeline(f"for (int i = 0; i < {cexpr_index(size)}; i++)")
                with code.indent():
                    code.writeline(f"tmpbuf_out[i] = {res};")
                load_args = f"tmpbuf_out.data(), {cexpr_index(size)}"
                if output_mask:
                    load_fn = f"at::vec::VecMask<{cdtype},{n_vec}>::from"
                elif n_vec == 1:
                    load_fn = f"at::vec::Vectorized<{octype}>::loadu"
                else:
                    load_fn = f" at::vec::VectorizedN<{octype}, {n_vec}>::loadu"
                code.writeline(f"return {load_fn}({load_args});")
            code.writeline("()")
            return code