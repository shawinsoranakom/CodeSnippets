def post_init(self):
        """
        A method executed at the end of each Transformer model initialization, to execute code that needs the model's
        modules properly initialized (such as weight initialization).
        It is also used to obtain all correct static properties (parallelism plans, tied_weights_keys, _keep_in_fp32_modules, etc)
        correctly in the case of composite models (that is, the top level model should know about those properties from its children).
        """
        # Attach the different parallel plans and tied weight keys to the top-most model, so that everything is
        # easily available
        self._tp_plan, self._ep_plan, self._pp_plan = {}, {}, {}
        # If current model is a base model, attach `base_model_tp_plan` and `base_model_pp_plan` from config
        if self.base_model is self:
            self._pp_plan = self.config.base_model_pp_plan.copy() if self.config.base_model_pp_plan is not None else {}
            self._tp_plan = self.config.base_model_tp_plan.copy() if self.config.base_model_tp_plan is not None else {}
            self._ep_plan = self.config.base_model_ep_plan.copy() if self.config.base_model_ep_plan is not None else {}
        # Current submodel should register its tied weights
        self.all_tied_weights_keys = self.get_expanded_tied_weights_keys(all_submodels=False)
        # Current submodel should register its `_keep_in_fp32_modules`
        self._keep_in_fp32_modules = set(self._keep_in_fp32_modules or [])
        self._keep_in_fp32_modules_strict = set(self._keep_in_fp32_modules_strict or [])
        # Current submodel must register its `_no_split_modules` as well
        self._no_split_modules = set(self._no_split_modules or [])

        # Iterate over children only: as the final model is created, this is enough to gather the properties from all submodels.
        # This works because the way the `__init__` and `post_init` are called on all submodules is depth-first in the graph
        for name, module in self.named_children():
            # Parallel plans
            if plan := getattr(module, "_ep_plan", None):
                self._ep_plan.update({f"{name}.{k}": v for k, v in plan.copy().items()})
            if plan := getattr(module, "_tp_plan", None):
                self._tp_plan.update({f"{name}.{k}": v for k, v in plan.copy().items()})
            if plan := getattr(module, "_pp_plan", None):
                self._pp_plan.update({f"{name}.{k}": v for k, v in plan.copy().items()})
            # Always attach the keys of the children (if the children's config says to NOT tie, then it's empty)
            if tied_keys := getattr(module, "all_tied_weights_keys", None):
                self.all_tied_weights_keys.update({f"{name}.{k}": f"{name}.{v}" for k, v in tied_keys.copy().items()})
            # Record keep_in_fp_32 modules from the children as well
            if keep_fp32 := getattr(module, "_keep_in_fp32_modules", None):
                self._keep_in_fp32_modules.update(keep_fp32)
            if keep_fp32_strict := getattr(module, "_keep_in_fp32_modules_strict", None):
                self._keep_in_fp32_modules_strict.update(keep_fp32_strict)
            # Record `_no_split_modules` from the children
            if no_split := getattr(module, "_no_split_modules", None):
                self._no_split_modules.update(no_split)

        # Maybe initialize the weights and tie the keys
        self.init_weights()
        self._backward_compatibility_gradient_checkpointing()