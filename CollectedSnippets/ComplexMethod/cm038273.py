def wrap_modules(
        self,
        modules_generator: Generator[nn.Module, None, None],
    ) -> list[nn.Module]:
        """Wrap modules with prefetch offloading logic."""
        assert len(self.module_offloaders) == 0, (
            "wrap_modules should only be called once"
        )

        all_modules = []
        offload_modules = []

        for module_index, module in enumerate(modules_generator):
            all_modules.append(module)

            # Select layers to offload based on group pattern
            # Offload last num_in_group layers of each group_size
            if module_index % self.group_size >= self.group_size - self.num_in_group:
                if self.offload_params:
                    whitelist = [
                        name
                        for name, _ in module.named_parameters()
                        if any(f".{p}." in f".{name}." for p in self.offload_params)
                    ]
                else:
                    whitelist = [name for name, _ in module.named_parameters()]

                if not whitelist:
                    continue  # skip layers with no matching params

                offload_modules.append(module)
                self.module_offloaders.append(
                    _ModuleOffloader(
                        mode=self.mode,
                        module=module,
                        copy_stream=self.copy_stream,
                        whitelist_param_names=whitelist,
                        layer_idx=len(self.module_offloaders),
                    )
                )

        for index, module in enumerate(offload_modules):
            self._hook_module_forward(index, module)

        return all_modules