def handle_synchronize(
            self,
            tx: "InstructionTranslator",
            *args: VariableTracker,
            **kwargs: VariableTracker,
        ) -> VariableTracker:
            device = None
            if kwargs and "device" in kwargs:
                device = torch.device(kwargs["device"].as_python_constant())
            elif args:
                device = torch.device(args[0].as_python_constant())

            if device is None:
                device_type = _synchronize_fn_to_device_type.get(self.value)
                if device_type is None:
                    # torch.accelerator.synchronize with no args
                    accelerator = torch.accelerator.current_accelerator()
                    assert accelerator is not None
                    device_type = accelerator.type
                device = torch.device(device_type)

            # CPU synchronize is a no-op, skip emitting the op
            if device.type == "cpu":
                return ConstantVariable.create(None)

            tx.output.create_proxy(
                "call_function",
                torch.ops.streams.synchronize_device,
                (device.type, device.index or 0),
                {},
            )
            return ConstantVariable.create(None)