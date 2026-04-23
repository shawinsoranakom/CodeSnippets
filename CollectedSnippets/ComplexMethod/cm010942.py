def __setstate__(self, state):
        super().__setstate__(state)
        for group in self.param_groups:
            group.setdefault("maximize", False)
            group.setdefault("foreach", None)
            group.setdefault("capturable", False)
            group.setdefault("differentiable", False)
            group.setdefault("decoupled_weight_decay", False)
            for p in group["params"]:
                p_state = self.state.get(p, [])
                if len(p_state) != 0:
                    if not torch.is_tensor(p_state["step"]):
                        step_val = float(p_state["step"])
                        p_state["step"] = (
                            torch.tensor(
                                step_val, dtype=_get_scalar_dtype(), device=p.device
                            )
                            if group["capturable"]
                            else torch.tensor(step_val, dtype=_get_scalar_dtype())
                        )
                    if not torch.is_tensor(p_state["mu_product"]):
                        mu_prod_val = p_state["mu_product"]
                        p_state["mu_product"] = (
                            torch.tensor(
                                mu_prod_val, dtype=_get_scalar_dtype(), device=p.device
                            )
                            if group["capturable"]
                            else torch.tensor(mu_prod_val, dtype=_get_scalar_dtype())
                        )