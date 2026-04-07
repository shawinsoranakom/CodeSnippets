def _show_deprecation_warning(self, message, category):
        stack = traceback.extract_stack()
        # Show a warning if the setting is used outside of Django.
        # Stack index: -1 this line, -2 the property, -3 the
        # LazyObject __getattribute__(), -4 the caller.
        filename, _, _, _ = stack[-4]
        if not filename.startswith(os.path.dirname(django.__file__)):
            warnings.warn(message, category, stacklevel=2)