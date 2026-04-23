def is_active(self, cls_name, test_name, device_type, dtype, param_kwargs):
        return (
            self.active_if
            and (self.cls_name is None or self.cls_name == cls_name)
            and (self.test_name is None or self.test_name == test_name)
            and (self.device_type is None or self.device_type == device_type)
            and (self.dtypes is None or dtype in self.dtypes)
            # Support callables over kwargs to determine if the decorator is active.
            and (
                self.active_if(param_kwargs)
                if isinstance(self.active_if, Callable)
                else self.active_if
            )
        )