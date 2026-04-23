def object_beta_warning(obj, obj_name, date):
    """Wrapper for objects that are no longer in beta.

    Wrapped objects will run as normal, but then proceed to show an st.warning
    saying that the beta_ version will be removed in ~3 months.

    Parameters
    ----------
    obj: Any
        The `st.` object that used to be in beta.

    obj_name: str
        The name of the object within __init__.py

    date: str
        A date like "2020-01-01", indicating the last day we'll guarantee
        support for the beta_ prefix.
    """

    has_shown_beta_warning = False

    def show_wrapped_obj_warning():
        nonlocal has_shown_beta_warning
        if not has_shown_beta_warning:
            has_shown_beta_warning = True
            _show_beta_warning(obj_name, date)

    class Wrapper:
        def __init__(self, obj):
            self._obj = obj

            # Override all the Wrapped object's magic functions
            for name in Wrapper._get_magic_functions(obj.__class__):
                setattr(
                    self.__class__,
                    name,
                    property(self._make_magic_function_proxy(name)),
                )

        def __getattr__(self, attr):
            # We handle __getattr__ separately from our other magic
            # functions. The wrapped class may not actually implement it,
            # but we still need to implement it to call all its normal
            # functions.
            if attr in self.__dict__:
                return getattr(self, attr)

            show_wrapped_obj_warning()
            return getattr(self._obj, attr)

        @staticmethod
        def _get_magic_functions(cls) -> List[str]:
            # ignore the handful of magic functions we cannot override without
            # breaking the Wrapper.
            ignore = ("__class__", "__dict__", "__getattribute__", "__getattr__")
            return [
                name
                for name in dir(cls)
                if name not in ignore and name.startswith("__")
            ]

        @staticmethod
        def _make_magic_function_proxy(name):
            def proxy(self, *args):
                show_wrapped_obj_warning()
                return getattr(self._obj, name)

            return proxy

    return Wrapper(obj)