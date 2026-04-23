def __call__(self, *args, **kwargs):
        config = getattr(self, "config", {})
        warning_filters = getattr(self, "warning_filters", [])
        if not config or not warning_filters:
            warnings.warn(
                (
                    "`sklearn.utils.parallel.delayed` should be used with"
                    " `sklearn.utils.parallel.Parallel` to make it possible to"
                    " propagate the scikit-learn configuration of the current thread to"
                    " the joblib workers."
                ),
                UserWarning,
            )

        with config_context(**config), warnings.catch_warnings():
            # TODO is there a simpler way that resetwarnings+ filterwarnings?
            warnings.resetwarnings()
            warning_filter_keys = ["action", "message", "category", "module", "lineno"]
            for filter_args in warning_filters:
                this_warning_filter_dict = {
                    k: v
                    for k, v in zip(warning_filter_keys, filter_args)
                    if v is not None
                }

                # Some small discrepancy between warnings filters and what
                # filterwarnings expect. simplefilter is more lenient, e.g.
                # accepts a tuple as category. We try simplefilter first and
                # use filterwarnings in more complicated cases
                if (
                    "message" not in this_warning_filter_dict
                    and "module" not in this_warning_filter_dict
                ):
                    warnings.simplefilter(**this_warning_filter_dict, append=True)
                else:
                    # 'message' and 'module' are most of the time regex.Pattern but
                    # can be str as well and filterwarnings wants a str
                    for special_key in ["message", "module"]:
                        this_value = this_warning_filter_dict.get(special_key)
                        if this_value is not None and not isinstance(this_value, str):
                            this_warning_filter_dict[special_key] = this_value.pattern

                    warnings.filterwarnings(**this_warning_filter_dict, append=True)

            return self.function(*args, **kwargs)