def _show_cached_st_function_warning(
        self,
        dg: "st.delta_generator.DeltaGenerator",
        st_func_name: str,
        cached_func: types.FunctionType,
    ) -> None:
        # Avoid infinite recursion by suppressing additional cached
        # function warnings from within the cached function warning.
        with self.suppress_cached_st_function_warning():
            e = CachedStFunctionWarning(self._cache_type, st_func_name, cached_func)
            dg.exception(e)