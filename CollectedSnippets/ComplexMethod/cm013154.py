def dep_fn(slf, *args, **kwargs):
            if (
                self.device_type is None
                or self.device_type == slf.device_type
                or (
                    isinstance(self.device_type, Iterable)
                    and slf.device_type in self.device_type
                )
            ):
                if (isinstance(self.dep, str) and getattr(slf, self.dep, True)) or (
                    isinstance(self.dep, bool) and self.dep
                ):
                    raise unittest.SkipTest(self.reason)

            return fn(slf, *args, **kwargs)