def _make_magic_function_proxy(name):
            def proxy(self, *args):
                show_wrapped_obj_warning()
                return getattr(self._obj, name)

            return proxy