def _get_store_line(
        self,
        value: str | CppCSEVariable,
        var: str,
        index: sympy.Expr,
        dtype: torch.dtype,
        accu_store: bool = False,
    ):
        """
        Get a store line buffer that stores `value` into `var` at `index` of `dtype`. It handles
        both contiguous and non-contiguous store cases.
        :param value: Vectorized type templaterized on `dtype`.
        :param var: buffer to store into.
        :index: index into the `var`.
        """
        # when value's type is str (e.g., welford reduction), caller should make sure
        # it is a vector
        assert isinstance(value, str) or (
            isinstance(value, CppCSEVariable) and value.is_vec
        ), value
        tiling_var = self.itervars[self.tiling_idx]
        var_expr = f"{var} + {cexpr_index(index)}"
        stride = self._try_get_const_stride(index, tiling_var)
        code = IndentedBuffer()
        if stride == 1:
            if accu_store:
                load = (
                    f"{self._get_vec_type(dtype)}::loadu({var_expr})"
                    if dtype == torch.float and self.tail_size is None
                    else f"{self._get_vec_type(dtype)}::loadu({var_expr}, {cexpr_index(self.num_elems)})"
                )
                value = f"({value} + {load})"
            if dtype == torch.float and self.tail_size is None:
                code.writeline(f"{value}.store({var_expr});")
            else:
                code.writeline(
                    f"{value}.store({var_expr}, {cexpr_index(self.num_elems)});"
                )
        else:
            self._load_or_store_non_contiguous(
                var, index, dtype, buffer=code, store_value=value, accu_store=accu_store
            )
        return code