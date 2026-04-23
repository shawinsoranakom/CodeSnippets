def _init_nested_model(
        self,
        wrap: bool,
        wrap_alt: bool = False,  # ignored if `wrap=False`
        device: torch.device = torch.device("cuda"),
        group=None,
        optim_class: type[torch.optim.Optimizer] = torch.optim.Adam,
        use_multiple_param_groups: bool = False,
        use_diff_optim_inputs: bool = False,
        fsdp_kwargs: dict[str, Any] | None = None,
    ):
        model = NestedModel().to(device)
        if wrap:
            model = (
                NestedModel.wrap_alt(model, group, fsdp_kwargs)
                if wrap_alt
                else NestedModel.wrap(model, group, fsdp_kwargs=fsdp_kwargs)
            )
        if not use_multiple_param_groups:
            optim_input = list(model.parameters())
        else:
            optim_input = [
                {"params": model.param_group0()},
                {"params": model.param_group1(), "weight_decay": 0.9},
            ]
        # Use a reversed parameter order for the optimizer input on odd ranks
        if use_diff_optim_inputs and self.rank % 2 == 1:
            if isinstance(optim_input[0], dict):
                for param_group in optim_input:
                    param_group["params"] = list(reversed(param_group["params"]))
            else:
                optim_input = list(reversed(optim_input))
        optim = optim_class(optim_input, lr=0.01)
        return model, optim, optim_input