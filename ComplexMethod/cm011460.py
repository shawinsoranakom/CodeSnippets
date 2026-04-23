def _fw_pre_hook(self, mod, input):
        """
        This function is called before the forward pass of a module. It
        collects the parameters and sharding information of a module and
        stores it in a dictionary.
        """
        if self.is_bw:
            self.activation_checkpointing = True
        else:
            self.activation_checkpointing = False

        self.name = super()._get_mod_name(mod)
        w_mod = weakref.ref(mod)

        # adds current sub-module to module tracker parent class
        super()._get_append_fn(w_mod, self.name, False)()

        args, _ = tree_flatten(input)
        tensors = [a for a in args if isinstance(a, torch.Tensor) and a.requires_grad]
        if not self.is_bw and tensors:
            register_multi_grad_hook(
                tensors, super()._get_pop_fn(w_mod, self.name, True)
            )

        if not self.activation_checkpointing:
            # contains information about module ordering and depth in the module tree
            if self.name not in self.module_helper_dict:
                self.module_helper_dict[self.name] = {}

            self.module_helper_dict[self.name]["module_type"] = (
                str(type(mod)).replace("<", "").replace(">", "")
            )
            self.module_helper_dict[self.name]["depth"] = len(self.parents) - 1

            for param_name, param in mod.named_parameters(recurse=False):
                if self.name not in self.module_parameters_dict:
                    self.module_parameters_dict[self.name] = {}

                self.module_parameters_dict[self.name][param_name] = param.data

                if isinstance(param.data, DTensor):
                    key_name = self.name + "." + param_name
                    self.sharding_dict[key_name] = param.data.placements

                    if "parameters" not in self.module_helper_dict[self.name]:
                        self.module_helper_dict[self.name]["parameters"] = {}

                    self.module_helper_dict[self.name]["parameters"][param_name] = str(
                        param.data.placements
                    )

            # used to store module's parents to ensure correctness in backward pass/checkpointing
            if self.name not in self.module_parents_dict:
                self.module_parents_dict[self.name] = copy.deepcopy(self.parents)

            # used to create parent-child module associations for json dumps
            parent = self.parent_list[-1]
            if parent not in self.parent_dict:
                self.parent_dict[parent] = []

            self.parent_dict[parent].append(self.name)
            self.parent_list.append(self.name)

            self.register_forward_hook_handles[self.name] = mod.register_forward_hook(
                self._fw_set_module_hook
            )