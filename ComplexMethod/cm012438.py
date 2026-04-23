def get_to_dtype_expr(self, src, dtype, src_dtype, rounding=False):
        assert isinstance(src, CppCSEVariable)
        if not src.is_vec:
            return super().get_to_dtype_expr(src, dtype, src_dtype, rounding)
        src_cpp_type = DTYPE_TO_CPP[src_dtype]
        src_num_vectors = self._get_num_vectors(src_dtype)
        dst_cpp_type = DTYPE_TO_CPP[dtype]
        dst_num_vectors = self._get_num_vectors(dtype)
        expr = f"({src})"
        if src_dtype != torch.bool and dtype == torch.bool:
            expr = f"{self._get_mask_type(src_dtype)}::from<{src_cpp_type},{src_num_vectors}>({src})"
        elif src_dtype == torch.bool and dtype != torch.bool:
            expr = f"{src}.to<{dst_cpp_type},{dst_num_vectors}>()"
        elif src_dtype != dtype:
            expr = ""
            if (
                rounding
                and src_dtype in [torch.float, torch.double]
                and dtype in [torch.int8, torch.uint8]
            ):
                expr = "at::vec::round_convert"
            else:
                expr = "at::vec::convert"
            if src_num_vectors == dst_num_vectors == 1:
                expr = expr + f"<{dst_cpp_type}>({src})"
            else:
                expr = (
                    expr
                    + f"<{dst_cpp_type},{dst_num_vectors},{src_cpp_type},{src_num_vectors}>({src})"
                )
        return expr