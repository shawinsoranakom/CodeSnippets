def _test_diff_ignored_modules_across_ranks(
        self,
        pass_ignored_modules_to_root: bool,
        ignore_modules: bool,
    ):
        # To exercise different `FlatParameter` enumerations across ranks,
        # we wrap `layer3` with FSDP, where `layer3` is registered as a module
        # after `layer1`, which has the variable number of ignored modules
        wrap_cls = FSDP
        model = ModelWithIgnoredModules(num_ignored=self.rank + 1).to(device_type)
        layer1_ignored_modules = [
            m for m in model.layer1.modules() if isinstance(m, IgnoredModule)
        ]
        ignore_kwargs = (
            {"ignored_modules": layer1_ignored_modules}
            if ignore_modules
            else {
                "ignored_states": (
                    p for m in layer1_ignored_modules for p in m.parameters()
                )
            }
        )
        model.layer1 = wrap_cls(model.layer1, **ignore_kwargs)
        model.layer3 = wrap_cls(model.layer3)
        model_ignored_modules = (
            [m for m in model.modules() if isinstance(m, IgnoredModule)]
            if pass_ignored_modules_to_root
            else []
        )
        ignore_kwargs_top = (
            {"ignored_modules": model_ignored_modules}
            if ignore_modules
            else {
                "ignored_states": {
                    p for m in model_ignored_modules for p in m.parameters()
                }
            }
        )
        wrapped_model = wrap_cls(model, **ignore_kwargs_top)
        optim = torch.optim.Adam(wrapped_model.parameters(), lr=1e-3)
        self._train_model(wrapped_model, optim, 3)