def _process_value_according_to_param_policy(
        param: torch.Tensor,
        value: torch.Tensor,
        param_id: int,
        param_groups: list[dict[Any, Any]],
        key: Hashable = None,
    ) -> torch.Tensor:
        # Floating-point types are a bit special here. They are the only ones
        # that are assumed to always match the type of params.
        # Make sure state['step'] is not casted https://github.com/pytorch/pytorch/issues/74424
        # UNLESS fused or capturable, see note [special device hosting for step]
        fused = False
        capturable = False
        if param_groups is None:
            raise AssertionError("Expected param_groups to be set")
        for pg in param_groups:
            if param_id in pg["params"]:
                fused = pg.get("fused", False)
                capturable = pg.get("capturable", False)
                break
        if key == "step":
            if capturable or fused:
                return value.to(dtype=torch.float32, device=param.device)
            else:
                return value
        else:
            if param.is_floating_point():
                return value.to(dtype=param.dtype, device=param.device)
            else:
                return value.to(device=param.device)