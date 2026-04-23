def _load_or_store_non_contiguous(
        self,
        var: str | None,
        index: sympy.Expr,
        dtype: torch.dtype,
        buffer: IndentedBuffer | None = None,
        store_value: str | CppCSEVariable | None = None,
        accu_store: bool = False,
    ) -> CppCSEVariable | None:
        """
        Load or store a vector in a non-contiguous way. The vector is initialized from an array that is
        filled in an inner loop over the tiling factor.
        :param var: buffer to load from or store to, i.e. `var[transformed(index)]`. If None, we load the index
                    as index expression, i.e. `transformed(index)`.
        :param index: index into the `var` or the index expression by its own if `var` is None.
                      The `index` could contain indirect indexing or the tiling itervar. When used in
                      the inner loop, the index is transformed as follows:
                      1. the index is linearized along the tiling dim.
                      2. the indirect indexing vector variables are transformed into arrays over the tiling dim.
        :param dtype: data type of `var` or `index` if `var` is None.
        :param buffer: the code buffer to write the generated code to. If None, we write to `self.loads`.
        :param store_value: the value to store. If None, we load the vector.
        :param accu_store: whether accumulate the store_value to store_ptr. If True, a store_value should be provided
        :return: a CppCSEVariable that represents the loaded vector or None if it is a store.
        """
        assert not store_value or var is not None, "store var must be provided"
        if accu_store:
            assert store_value
        if buffer is None:
            buffer = self.loads

        def get_result_size(dtype: torch.dtype) -> int:
            if dtype.itemsize < 4:
                return self.num_elems * (4 // dtype.itemsize)
            else:
                return self.num_elems

        def get_tiling_size(dtype: torch.dtype) -> int:
            if dtype.itemsize < 4:
                return self.tiling_factor * (4 // dtype.itemsize)
            else:
                return self.tiling_factor

        def vec_to_array(vec_var: CppCSEVariable) -> CppCSEVariable:
            assert vec_var.is_vec
            code = BracesBuffer()
            code.writeline("[&]")
            with code.indent():
                vec_dtype = vec_var.dtype
                assert vec_dtype is not None
                if vec_dtype == torch.bool:
                    vec_dtype = torch.float
                result_size = get_result_size(vec_dtype)
                tiling_size = get_tiling_size(vec_dtype)
                code.writeline(
                    f"__at_align__ std::array<{DTYPE_TO_CPP[vec_dtype]}, {tiling_size}> tmpbuf;"
                )
                line = f"{vec_var}.store(tmpbuf.data(), {cexpr_index(result_size)});"
                code.writeline(line)
                code.writeline("return tmpbuf;")
            code.writeline("()")
            csevar = self.cse.generate(buffer, code)
            assert isinstance(csevar, CppCSEVariable)
            return csevar

        code = BracesBuffer()
        code.writeline("[&]")
        with code.indent():
            result_size = get_result_size(dtype)
            tiling_size = get_tiling_size(dtype)
            result_declare = (
                f"__at_align__ std::array<{DTYPE_TO_CPP[dtype]}, {tiling_size}> tmpbuf;"
            )
            code.writeline(result_declare)
            if store_value:
                code.writeline(
                    f"{store_value}.store(tmpbuf.data(), {cexpr_index(result_size)});"
                )
            itervar_inner = sympy_index_symbol(
                f"{self.itervars[self.tiling_idx]}_inner"
            )
            replacements = {}
            for indirect_var in (
                self.cse.varname_map[s.name]  # type: ignore[attr-defined]
                for s in index.free_symbols
                if symbol_is_type(s, SymT.TMP)
            ):
                assert isinstance(indirect_var, CppCSEVariable)
                if indirect_var.is_vec:
                    array_var = vec_to_array(indirect_var)
                    replacements[indirect_var] = f"{array_var}[{itervar_inner}]"
            index = self.scale_index_with_offset(
                index, itervar_idx=self.tiling_idx, offset=itervar_inner
            )
            load_mask = None
            if self._load_mask is not None:
                assert not store_value, "unexpected store with load mask"
                assert isinstance(self._load_mask, CppCSEVariable), self._load_mask
                if self._load_mask.is_vec:
                    load_mask = f"{self._load_mask}.is_masked({itervar_inner})"
                else:
                    load_mask = f"{self._load_mask} != 0"
            if cpp_builder.is_gcc():
                code.writeline(f"#pragma GCC unroll {self.tiling_factor}")
            else:
                code.writeline(f"#pragma unroll {self.tiling_factor}")
            code.writeline(
                f"for (long {itervar_inner} = 0; "
                + f"{itervar_inner} < {cexpr_index(self.num_elems)}; "
                + f"{itervar_inner}++)"
            )
            with code.indent(), contextlib.ExitStack() as stack:
                index_c = cexpr_index(index)
                # pyrefly: ignore [bad-assignment]
                for indirect_var in replacements:
                    index_c = re.sub(
                        r"\b" + f"{indirect_var}" + r"\b",
                        replacements[indirect_var],
                        index_c,
                    )
                rhs = f"{var}[{index_c}]" if var is not None else f"{index_c}"
                if load_mask:
                    code.writeline(f"if ({load_mask})")
                    stack.enter_context(code.indent())
                if store_value:
                    conjunction = "+=" if accu_store else "="
                    code.writeline(f"{rhs} {conjunction} tmpbuf[{itervar_inner}];")
                else:
                    code.writeline(f"tmpbuf[{itervar_inner}] = {rhs};")
            if not store_value:
                load_line = self._get_vec_load_line("tmpbuf.data()", 0, dtype)  # type: ignore[arg-type]
                code.writeline(f"return {load_line};")
        code.writeline("()")
        if store_value:
            code.writeline(";")
            buffer.splice(code)
            return None
        else:
            csevar = self.cse.generate(buffer, code, dtype=dtype)
            assert isinstance(csevar, CppCSEVariable)
            csevar.is_vec = True
            return csevar