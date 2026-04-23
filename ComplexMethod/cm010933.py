def add_param_group(self, param_group: dict[str, Any]) -> None:
        r"""Add a param group to the :class:`Optimizer` s `param_groups`.

        This can be useful when fine tuning a pre-trained network as frozen layers can be made
        trainable and added to the :class:`Optimizer` as training progresses.

        Args:
            param_group (dict): Specifies what Tensors should be optimized along with group
                specific optimization options.
        """
        if not isinstance(param_group, dict):
            raise TypeError(f"param_group must be a dict, but got {type(param_group)}")

        params = param_group["params"]
        if isinstance(params, torch.Tensor):
            param_group["params"] = [params]
        elif isinstance(params, set):
            raise TypeError(
                "optimizer parameters need to be organized in ordered collections, but "
                "the ordering of tensors in sets will change between runs. Please use a list instead."
            )
        else:
            param_group["params"] = list(params)

        extracted_param_tensors = []
        extracted_param_names = []
        for param in param_group["params"]:
            if isinstance(param, tuple):
                param_name = param[0]
                extracted_param_names.append(param_name)
                extracted_param_tensors.append(param[1])
            else:
                extracted_param_tensors.append(param)

        param_group["params"] = extracted_param_tensors
        if len(extracted_param_names) != 0:
            if len(extracted_param_names) == len(extracted_param_tensors):
                param_group["param_names"] = extracted_param_names
            else:
                raise ValueError(
                    "all optimizer params should be with/without names. Some param names are missing"
                )

        for param in param_group["params"]:
            if not isinstance(param, torch.Tensor):
                raise TypeError(
                    "optimizer can only optimize Tensors, "
                    "but one of the params is " + torch.typename(param)
                )
            if not self.defaults.get("differentiable", None) and not (
                param.is_leaf or param.retains_grad
            ):
                raise ValueError("can't optimize a non-leaf Tensor")

        for name, default in self.defaults.items():
            if default is required and name not in param_group:
                raise ValueError(
                    f"parameter group didn't specify a value of required optimization parameter {name}"
                )
            else:
                param_group.setdefault(name, default)

        params = param_group["params"]
        if len(params) != len(set(params)):
            warnings.warn(
                "optimizer contains a parameter group with duplicate parameters; "
                "in future, this will cause an error; "
                "see github.com/pytorch/pytorch/issues/40967 for more information",
                stacklevel=3,
            )

        param_set: set[torch.Tensor] = set()
        for group in self.param_groups:
            param_set.update(set(group["params"]))
            if ("param_names" in param_group) != ("param_names" in group):
                current_group_txt = (
                    "with names" if "param_names" in param_group else "without names"
                )
                raise ValueError(
                    "all optimizer param groups should be with/without names. "
                    f"cannot add param group {current_group_txt} to the optimizer"
                )

        if not param_set.isdisjoint(set(param_group["params"])):
            raise ValueError("some parameters appear in more than one parameter group")

        self.param_groups.append(param_group)