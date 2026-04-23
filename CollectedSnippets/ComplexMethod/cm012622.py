def cse_multiple(line, broadcasted_values, masks, dtypes):
            n = len(broadcasted_values)
            cache_keys = [f"{line}, {i}, {masks}" for i in range(n)]
            if all(self.cse.contains(cache_key) for cache_key in cache_keys):
                return [self.cse.get(cache_key) for cache_key in cache_keys]
            result_vars = [
                self.cse.newvar(dtype=dtype, shape=value.shape)
                for dtype, value in zip(dtypes, broadcasted_values)
            ]  # type: ignore[attr-defined]
            self.compute.writeline(
                f"{csv(result_vars)} = {line}",
            )
            for result_var, cache_key in zip(result_vars, cache_keys):
                if masks:
                    result_var.mask_vars = masks  # type: ignore[attr-defined]
                self.cse.put(cache_key, result_var)
            return tuple(result_vars)