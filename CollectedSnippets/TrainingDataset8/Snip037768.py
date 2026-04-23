def maybe_show_cached_st_function_warning(
        self,
        dg: "st.delta_generator.DeltaGenerator",
        st_func_name: str,
    ) -> None:
        """If appropriate, warn about calling st.foo inside @memo.

        DeltaGenerator's @_with_element and @_widget wrappers use this to warn
        the user when they're calling st.foo() from within a function that is
        wrapped in @st.cache.

        Parameters
        ----------
        dg : DeltaGenerator
            The DeltaGenerator to publish the warning to.

        st_func_name : str
            The name of the Streamlit function that was called.

        """
        # There are some elements not in either list, which we still want to warn about.
        # Ideally we will fix this by either updating the lists or creating a better
        # way of categorizing elements.
        if st_func_name in NONWIDGET_ELEMENTS:
            return
        if st_func_name in WIDGETS and self._allow_widgets > 0:
            return

        if len(self._cached_func_stack) > 0 and self._suppress_st_function_warning <= 0:
            cached_func = self._cached_func_stack[-1]
            self._show_cached_st_function_warning(dg, st_func_name, cached_func)