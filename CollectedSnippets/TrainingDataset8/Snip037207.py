def proxy(self, *args):
                show_wrapped_obj_warning()
                return getattr(self._obj, name)