def device_time_total(self):
        if self.is_async or not self.use_device:
            return 0
        if self.device_type == DeviceType.CPU:
            if not self.is_legacy:
                # account for the kernels in the children ops
                return sum(kinfo.duration for kinfo in self.kernels) + sum(
                    ch.device_time_total for ch in self.cpu_children
                )
            else:
                # each legacy cpu events has a single (fake) kernel
                return sum(kinfo.duration for kinfo in self.kernels)
        else:
            if self.device_type not in [
                DeviceType.CUDA,
                DeviceType.PrivateUse1,
                DeviceType.MTIA,
                DeviceType.HPU,
                DeviceType.XPU,
            ]:
                raise AssertionError(
                    f"Expected device_type to be CUDA, PrivateUse1, MTIA, HPU or XPU, but got {self.device_type}"
                )
            return self.time_range.elapsed_us()