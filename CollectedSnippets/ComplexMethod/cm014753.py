def _test_functional_optim_parity(self, optim_cls, *args, **kwargs):
        module_optim = MyModule()
        module_functional = MyModule()
        optim_params = module_optim.parameters()
        optim = optim_cls(optim_params, *args, **kwargs)
        functional_optim_cls = functional_optim_map.get(optim_cls, None)
        if not functional_optim_cls:
            raise ValueError(f"Functional optimizer not implemented for {optim_cls}")
        optim_functional = functional_optim_cls(
            [], *args, **kwargs, _allow_empty_param_list=True
        )
        if not hasattr(optim_functional, "step_param"):
            raise ValueError(
                f"Functional optimizer class {optim_functional} must implement step_param method."
            )

        # Initial weights should match
        self._validate_parameters(
            module_optim.parameters(), module_functional.parameters()
        )
        # Save old parameters to verify optimizer modifies them.
        old_module_optim_params = [
            param.detach().clone() for param in module_optim.parameters()
        ]
        old_module_functional_params = [
            param.detach().clone() for param in module_functional.parameters()
        ]

        t1 = torch.randn(3, 3)
        for _ in range(10):
            module_optim.zero_grad()
            module_functional.zero_grad()
            # Forward + Backward
            optim_out = module_optim(t1).sum()
            functional_out = module_functional(t1).sum()
            optim_out.backward()
            functional_out.backward()
            # Optimizer step
            optim.step()
            # Functional optimizer step_param
            for param in module_functional.parameters():
                grad = param.grad
                optim_functional.step_param(param, grad)

            # Validate parameters are equal
            for optim_param, functional_param in zip(
                module_optim.parameters(), module_functional.parameters()
            ):
                self.assertEqual(optim_param, functional_param)
            # Validate parameters are modified.
            for i, (optim_param, functional_param) in enumerate(
                zip(module_optim.parameters(), module_functional.parameters())
            ):
                self.assertNotEqual(old_module_optim_params[i], optim_param)
                self.assertNotEqual(old_module_functional_params[i], functional_param)