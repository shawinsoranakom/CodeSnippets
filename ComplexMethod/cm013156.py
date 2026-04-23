def efail_fn(slf, *args, **kwargs):
            if (
                not hasattr(slf, "device_type")
                and hasattr(slf, "device")
                and isinstance(slf.device, str)
            ):
                target_device_type = slf.device
            else:
                target_device_type = slf.device_type

            target_dtype = kwargs.get("dtype", getattr(slf, "dtype", None))
            device_matches = (
                self.device_type is None or self.device_type == target_device_type
            )
            dtype_matches = self.dtype is None or self.dtype == target_dtype

            if device_matches and dtype_matches:
                try:
                    fn(slf, *args, **kwargs)
                except Exception:
                    return
                else:
                    slf.fail("expected test to fail, but it passed")

            return fn(slf, *args, **kwargs)