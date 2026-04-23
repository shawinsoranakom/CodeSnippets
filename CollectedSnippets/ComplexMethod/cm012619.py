def is_where_needed(var):
            # Skip if the variable doesn't have a reduction mask
            if not any(map(prefix_is_reduction, var.mask_vars)):
                return False

            reduction_range = V.kernel.range_trees[-1]
            assert reduction_range.is_reduction

            # Skip if reduction mask was already constant
            if V.kernel._has_constant_mask(reduction_range):
                return False

            # Skip if the variable is already zeroed outside the mask
            # (e.g., from tl.load(..., other=0.0))
            # TODO : track the value of outside of mask region with cse
            for k, v in V.kernel.cse._cache.items():
                if v == var and "tl.load" in k and "other=0.0" in k:
                    return False

            return True