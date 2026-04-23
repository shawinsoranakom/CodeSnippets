def handle_get_device_module(
            self,
            tx: "InstructionTranslator",
            *args: VariableTracker,
            **kwargs: VariableTracker,
        ) -> VariableTracker:
            if len(args) + len(kwargs) > 1 or (kwargs and "device" not in kwargs):
                unimplemented(
                    gb_type="improper torch.get_device_module arguments",
                    context=f"args={args}, kwargs={kwargs}",
                    explanation="torch.get_device_module accepts 1 optional argument `device`",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )
            try:
                if kwargs:
                    device = kwargs["device"].as_python_constant()
                elif args:
                    device = args[0].as_python_constant()
                else:
                    device = None
                module = torch.get_device_module(device)
            except Exception as e:
                unimplemented(
                    gb_type="bad device argument to torch.get_device_module",
                    context=f"args={args}, kwargs={kwargs}",
                    explanation="Expected valid string/torch.device argument ('cpu', 'cuda', etc.)",
                    hints=[*graph_break_hints.USER_ERROR],
                    from_exc=e,
                )

            # need to guard only on no-arg get_device_module
            if device is None:
                source = CallFunctionNoArgsSource(self.source)
                install_guard(source.make_guard(GuardBuilder.ID_MATCH))
            # assumes `module` is in the form `torch.xyz`
            new_source = AttrSource(
                ImportSource("torch"),
                module.__name__.rsplit(".", maxsplit=1)[-1],
            )
            return VariableTracker.build(tx, module, new_source)