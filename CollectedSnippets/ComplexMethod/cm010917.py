def __setstate__(self, state):
        super().__setstate__(state)
        #  define "fused" for
        #  MYPY error: Name "fused" may be undefined
        fused = None
        for group in self.param_groups:
            group.setdefault("foreach", None)
            group.setdefault("maximize", False)
            group.setdefault("differentiable", False)
            fused = group.setdefault("fused", None)

            for p in group["params"]:
                p_state = self.state.get(p, [])
                if len(p_state) != 0 and not torch.is_tensor(p_state["step"]):
                    step_val = float(p_state["step"])
                    p_state["step"] = (
                        torch.tensor(
                            step_val,
                            dtype=_get_scalar_dtype(is_fused=fused),
                            device=p.device,
                        )
                        if group["fused"]
                        else torch.tensor(step_val, dtype=_get_scalar_dtype())
                    )

        state_values = list(self.state.values())
        step_is_tensor = (len(state_values) != 0) and torch.is_tensor(
            state_values[0]["step"]
        )
        if not step_is_tensor:
            for s in state_values:
                s["step"] = torch.tensor(
                    float(s["step"]), dtype=_get_scalar_dtype(is_fused=fused)
                )