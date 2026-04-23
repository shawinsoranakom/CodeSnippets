def make_val(
                x: Argument,
            ) -> (
                FakeTensor
                | torch.SymInt
                | torch.SymFloat
                | torch.SymBool
                | int
                | float
                | bool
                | str
                | None
            ):
                if isinstance(x, FakeTensor):
                    return x
                elif isinstance(x, torch.Tensor):
                    if x.is_quantized:
                        # TODO (tmanlaibaatar) properly support Quantized FakeTensor
                        x = torch.dequantize(x)

                    try:
                        if self.fake_tensor_mode is None:
                            raise AssertionError("fake_tensor_mode must not be None")
                        # TODO we should allocate static shapes
                        # for param/buffer values
                        if isinstance(x, torch.nn.Parameter):
                            fake_tensor = self.fake_tensor_mode.from_tensor(
                                x, static_shapes=True
                            )
                        else:
                            fake_tensor = self.fake_tensor_mode.from_tensor(x)
                    except UnsupportedFakeTensorException:
                        # TODO: This is just a workaround to get over the
                        # x.as_subclass error
                        print(
                            "Fakeifying a Tensor subclass is not supported \
                            right now. Instead a TensorMetadata is used."
                        )
                        fake_tensor = None
                    return fake_tensor
                elif isinstance(
                    x,
                    (
                        torch.SymInt,
                        torch.SymFloat,
                        torch.SymBool,
                        int,
                        float,
                        bool,
                        str,
                    ),
                ):
                    return x
                else:
                    return None