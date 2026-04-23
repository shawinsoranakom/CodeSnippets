def load_state_dict(self, state_dict: dict[str, Any], strict: bool = True):
        groups = copy.deepcopy(state_dict["groups"])
        states = state_dict["state"]
        for tensor_fqn, s in states.items():
            arg_info = get_arg_info_from_tensor_fqn(self.model, tensor_fqn)
            module = arg_info["module"]
            tensor_name = arg_info["tensor_name"]
            if strict and module is None:
                raise RuntimeError(f"Error loading {tensor_fqn} into the model")

            found = False
            for p in module.parametrizations[tensor_name]:
                if isinstance(p, FakeSparsity):
                    found = True
                    break
            if not found:
                p = FakeSparsity(torch.ones(getattr(module, tensor_name).shape))
                parametrize.register_parametrization(module, tensor_name, p)
            if s.get("mask", None) is not None:
                mask = s.pop("mask")
                p.mask = mask

            for mg in groups:
                if mg["tensor_fqn"] == tensor_fqn:
                    mg.update(arg_info)
        self.__setstate__({"state": states, "groups": groups})