def _load_module(
        self,
        base_prefix: str,
        module: nn.Module,
        weights: Iterable[tuple[str, torch.Tensor]],
    ) -> Iterable[str]:
        if isinstance(module, (StageMissingLayer, PPMissingLayer)):
            return

        # Avoid infinite recursion since this function is typically
        # called inside load_weights of the module itself
        if module != self.module:
            module_load_weights = getattr(module, "load_weights", None)
            if callable(module_load_weights):
                loaded_params = module_load_weights(weights)
                if loaded_params is None:
                    logger.warning(
                        "Unable to collect loaded parameters for module %s", module
                    )
                else:
                    yield from map(
                        lambda x: self._get_qualname(base_prefix, x),
                        loaded_params,
                    )

        child_modules = dict(module.named_children())
        child_params = dict(module.named_parameters(recurse=False))

        # Add missing tensors the weight loader needs to be able to load
        # that aren't registered as params, e.g., batchnorm statistics.
        self._add_loadable_non_param_tensors(module, child_params)

        for child_prefix, child_weights in self._groupby_prefix(weights):
            prefix = self._get_qualname(base_prefix, child_prefix)

            if child_prefix in child_modules:
                if self._can_skip(prefix + "."):
                    logger.debug("Skipping module %s", prefix)

                    continue

                yield from self._load_module(
                    prefix, child_modules[child_prefix], child_weights
                )
            elif child_prefix in child_params:
                if self._can_skip(prefix):
                    logger.debug("Skipping param %s", prefix)

                    continue

                yield from self._load_param(
                    prefix, child_params[child_prefix], child_weights
                )
            else:
                can_skip_module = self._can_skip(prefix + ".")
                can_skip_param = self._can_skip(prefix)
                if can_skip_module or can_skip_param:
                    logger.debug("Skipping missing %s", prefix)

                    continue

                can_ignore_module = self._can_ignore_unexpected(prefix + ".")
                can_ignore_param = self._can_ignore_unexpected(prefix)
                if can_ignore_module or can_ignore_param:
                    logger.debug("Ignoring missing %s", prefix)

                    continue

                named_parameters = module.named_parameters(recurse=True)
                desc_param_keys = {
                    maybe_prefix(base_prefix, k) for k, _ in named_parameters
                }
                msg = (
                    f"There is no module or parameter named {prefix!r} "
                    f"in {self.module._get_name()}. "
                    f"The available parameters belonging to {base_prefix} "
                    f"({module._get_name()}) are: {desc_param_keys}"
                )
                raise ValueError(msg)