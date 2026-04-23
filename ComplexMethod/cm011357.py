def _unflatten_model_state_dict(
    model: nn.Module,
    state_dict: dict[nn.Module, dict[str, ValueType]] | dict[str, ValueType],
) -> dict[str, ValueType]:
    if not state_dict:
        return {}

    if isinstance(next(iter(state_dict.keys())), nn.Module):
        warnings.warn(
            "Passing model_state_dict as a ``Dict[nn.Module, Dict[str, Any]]``"
            "is deprecated and will be removed in 2.5. If you need this "
            "feature, please preprocessing the model_state_dict to achieve the "
            "same functionality.",
            FutureWarning,
            stacklevel=2,
        )
        cast_state_dict = cast(dict[nn.Module, dict[str, ValueType]], state_dict)
        new_state_dict: dict[str, ValueType] = {}
        for submodule, sub_state_dict in cast_state_dict.items():
            for name, m in model.named_modules():
                if m != submodule:
                    continue

                fqns = _get_fqns(model, name)
                if len(fqns) != 1:
                    raise AssertionError(
                        "FQNs for a submodule should only have 1 element"
                    )
                prefix = f"{next(iter(fqns))}."
                new_state_dict.update(
                    {prefix + subfqn: value for subfqn, value in sub_state_dict.items()}
                )
        return new_state_dict
    else:
        return cast(dict[str, ValueType], state_dict)