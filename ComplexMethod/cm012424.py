def masked(mask, body, other):
        assert isinstance(V.kernel, CppVecKernel)
        code = BracesBuffer()
        var = V.kernel.cse.newvar()
        with V.kernel.masked(mask) as new_mask:
            code.writeline(f"auto {var} = [&]")
            with V.kernel.swap_buffers(code), code.indent():
                result = body()
                code.writeline(f"return {result};")
        code.writeline(";")
        V.kernel.compute.splice(code)

        dtype = result.dtype
        body_code = f"{var}()"

        def maskify_or_vecify(code):
            return (
                f"{V.kernel._get_mask_type()}::from({code})"
                if dtype == torch.bool
                else f"{V.kernel._get_vec_type(dtype)}({code})"
            )

        if result.is_vec:
            body_code_vec = body_code
        else:
            body_code_vec = maskify_or_vecify(body_code)
        other_code = value_to_cpp(other, DTYPE_TO_CPP[dtype])
        # loading bool as VecMask<float, N>
        other_code_vec = maskify_or_vecify(other_code)
        assert isinstance(new_mask, CppCSEVariable), new_mask
        if new_mask.is_vec:
            code = BracesBuffer()
            code.writeline("[&]")
            with V.kernel.swap_buffers(code), code.indent():
                code.writeline(f"if ({new_mask}.all_zero())")
                with code.indent():
                    code.writeline(f"return {other_code_vec};")
                code.writeline("else")
                with code.indent():
                    # Create cse variable to reuse kernel.overrides.where
                    body_vec_var = V.kernel.cse.generate(
                        V.kernel.compute,
                        body_code_vec,
                    )
                    other_vec_var = V.kernel.cse.generate(
                        V.kernel.compute,
                        other_code_vec,
                    )
                    assert isinstance(body_vec_var, CppCSEVariable), body_vec_var
                    assert isinstance(other_vec_var, CppCSEVariable), other_vec_var
                    body_vec_var.dtype = dtype
                    other_vec_var.dtype = dtype
                    overrides: type[CppOverrides | CppVecOverrides] = (
                        # pyrefly: ignore [bad-assignment]
                        V.kernel.overrides
                    )  # type: ignore[has-type]
                    code.writeline(
                        f"return {overrides.where(new_mask, body_vec_var, other_vec_var)};"
                    )
            code.writeline("()")
            csevar = V.kernel.cse.generate(
                V.kernel.compute,
                code,
            )
            assert isinstance(csevar, CppCSEVariable)
            csevar.is_vec = True
        elif result.is_vec:
            csevar = V.kernel.cse.generate(
                V.kernel.compute, f"{mask} ? {body_code_vec} : {other_code_vec}"
            )
        else:
            csevar = V.kernel.cse.generate(
                V.kernel.compute, f"{mask} ? {body_code} : {other_code}"
            )
        # `result` is explicitly added to the args for correct propagation
        # of relevant itervars and vectorization status.
        csevar.update_on_args("masked", (mask, body, other, result), {})
        return csevar