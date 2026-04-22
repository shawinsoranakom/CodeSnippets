def __call__(self, get_val_func: Callable[[], Any]) -> "ConfigOption":
        """Assign a function to compute the value for this option.

        This method is called when ConfigOption is used as a decorator.

        Parameters
        ----------
        get_val_func : function
            A function which will be called to get the value of this parameter.
            We will use its docString as the description.

        Returns
        -------
        ConfigOption
            Returns self, which makes testing easier. See config_test.py.

        """
        assert (
            get_val_func.__doc__
        ), "Complex config options require doc strings for their description."
        self.description = get_val_func.__doc__
        self._get_val_func = get_val_func
        return self