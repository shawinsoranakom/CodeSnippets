def _param_groups_check(self) -> None:
        if self.param_groups is not None:
            for param_group in self.param_groups:
                if not isinstance(param_group, dict):
                    raise AssertionError("param group must be a dict")
                if "params" not in param_group:
                    raise AssertionError("param group must contain key params")
                params = param_group["params"]
                if isinstance(params, torch.Tensor):
                    params = [params]
                params = list(params)
                for param in params:
                    if not isinstance(param, torch.Tensor):
                        raise TypeError(
                            "optimizer can only optimize Tensors, "
                            "but one of the params is " + torch.typename(param)
                        )
                param_group["params"] = params