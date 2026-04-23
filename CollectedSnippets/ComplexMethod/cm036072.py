def wrap_device(self, x: _T, device: str | None = None) -> _T:
        if x is None or isinstance(x, (bool,)):
            return x

        if device is None:
            device = self.device

        if isinstance(x, dict):
            return {k: self.wrap_device(v, device) for k, v in x.items()}

        if hasattr(x, "device") and x.device.type == device:
            return x

        return x.to(device)