def pyplot(
        self,
        fig: Optional["Figure"] = None,
        clear_figure: Optional[bool] = None,
        **kwargs: Any,
    ) -> "DeltaGenerator":
        """Display a matplotlib.pyplot figure.

        Parameters
        ----------
        fig : Matplotlib Figure
            The figure to plot. When this argument isn't specified, this
            function will render the global figure (but this is deprecated,
            as described below)

        clear_figure : bool
            If True, the figure will be cleared after being rendered.
            If False, the figure will not be cleared after being rendered.
            If left unspecified, we pick a default based on the value of `fig`.

            * If `fig` is set, defaults to `False`.

            * If `fig` is not set, defaults to `True`. This simulates Jupyter's
              approach to matplotlib rendering.

        **kwargs : any
            Arguments to pass to Matplotlib's savefig function.

        Example
        -------
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>>
        >>> arr = np.random.normal(1, 1, size=100)
        >>> fig, ax = plt.subplots()
        >>> ax.hist(arr, bins=20)
        >>>
        >>> st.pyplot(fig)

        .. output::
           https://doc-pyplot.streamlitapp.com/
           height: 630px

        Notes
        -----
        .. note::
           Deprecation warning. After December 1st, 2020, we will remove the ability
           to specify no arguments in `st.pyplot()`, as that requires the use of
           Matplotlib's global figure object, which is not thread-safe. So
           please always pass a figure object as shown in the example section
           above.

        Matplotlib supports several types of "backends". If you're getting an
        error using Matplotlib with Streamlit, try setting your backend to "TkAgg"::

            echo "backend: TkAgg" >> ~/.matplotlib/matplotlibrc

        For more information, see https://matplotlib.org/faq/usage_faq.html.

        """

        if not fig and config.get_option("deprecation.showPyplotGlobalUse"):
            self.dg.exception(PyplotGlobalUseWarning())

        image_list_proto = ImageListProto()
        marshall(
            self.dg._get_delta_path_str(), image_list_proto, fig, clear_figure, **kwargs
        )
        return self.dg._enqueue("imgs", image_list_proto)