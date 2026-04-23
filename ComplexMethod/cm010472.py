def __new__(
        cls,
        fake_mode: FakeTensorMode,
        elem: Tensor,
        device: torch.device,
        constant: Tensor | None = None,
        real_tensor: Tensor | None = None,
        pytype: type[Tensor] | None = None,
        dispatch_keys: torch.DispatchKeySet | None = None,
    ) -> Self:
        self = Tensor._make_subclass(
            cls,
            elem,
            elem.requires_grad,
            dispatch_device=True,
            device_for_backend_keys=device,
        )
        if not fake_mode._allow_unsafe_data_ptr_access:
            torch._C._set_throw_on_mutable_data_ptr(self)
        else:
            torch._C._set_warn_deprecated_on_mutable_data_ptr(self)

        if elem.device.type != "meta":
            raise AssertionError(
                f"elem.device.type must be 'meta', got {elem.device.type}"
            )
        device = device if isinstance(device, torch.device) else torch.device(device)
        # NB: it is fine, if a little confusing, for device to be meta
        # (we are faking a meta tensor in that case).  However, it often
        # indicates some sort of confusion (e.g., you accidentally passed
        # in a meta tensor when you should have passed in the real tensor).
        # So by default we disallow meta, and if you are working in a situation
        # where it is helpful (e.g., crossref testing) you can turn it back
        # on
        if not fake_mode.allow_meta:
            if device.type == "meta":
                raise AssertionError(
                    "device.type must not be 'meta' when allow_meta is False"
                )
        self.fake_device = device
        self.fake_mode = fake_mode
        self.constant = constant
        self.pytype = pytype
        self.dispatch_keys = dispatch_keys
        if isinstance(real_tensor, FakeTensor):
            raise AssertionError("real_tensor must not be a FakeTensor")
        self.real_tensor = real_tensor
        self.nonzero_memo = None
        self.item_memo = None
        self.unique_memo = None
        self.unique_consecutive_memo = None
        self.nested_int_memo = None

        if FakeTensorConfig.debug:
            self._debug_trace = CapturedTraceback.extract()  # type: ignore[attr-defined]
        return self