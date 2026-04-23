def reduction_init_vec(self, reduction_type, dtype):
        scalar_type = DTYPE_TO_COMPUTATION_DTYPE[dtype]
        vec_type = self._get_vec_type(scalar_type)

        if is_welford_reduction(reduction_type):
            return f"Welford<{vec_type}>()"

        if reduction_type in ("argmin", "argmax"):
            # For bool argmin/argmax, we use float for computations
            compute_dtype = torch.float if dtype == torch.bool else scalar_type
            cdtype = DTYPE_TO_CPP[compute_dtype]
            acc_type = self.reduction_acc_type_vec(reduction_type, dtype)
            if reduction_type == "argmin":
                val = (
                    f"std::numeric_limits<{cdtype}>::infinity()"
                    if is_float_dtype(dtype) or dtype == torch.bool
                    else f"std::numeric_limits<{cdtype}>::max()"
                )
            else:
                val = (
                    f"-std::numeric_limits<{cdtype}>::infinity()"
                    if is_float_dtype(dtype) or dtype == torch.bool
                    else f"std::numeric_limits<{cdtype}>::min()"
                )
            return f"{acc_type}({val})"

        if reduction_type == "any":
            return f"{self._get_mask_type()}::from(0)"

        scalar_init = reduction_init(reduction_type, dtype)
        vec_init = f"{vec_type}({scalar_init})"
        if dtype == torch.bool:
            assert reduction_type in ("min", "max", "sum")
            return f"{self._get_mask_type()}::from({scalar_init})"
        return vec_init