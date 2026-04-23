def wrapped(
        *args: Any, **kwargs: Any
    ) -> (
        tuple[
            tuple[Tensor, ...],
            tuple[Tensor, ...],
            Callable[..., Any],
            tuple[str, ...],
            tuple[str, ...],
        ]
        | tuple[tuple[Tensor, ...], Callable[..., Any], tuple[str, ...]]
    ):
        if len(ensemble_shape) >= 2:
            raise ValueError("NYI: ensemble_shape with more than 1 element")
        if len(ensemble_shape) == 0:
            model = model_class(*args, **kwargs).to(device)
            return make_functional_deprecated_v1(model)
        num_models = ensemble_shape[0]  # type: ignore[misc]
        if num_models <= 0:
            raise ValueError(f"num_models {num_models} should be > 0")
        # NB: Not very efficient, more of a POC
        models = tuple(
            model_class(*args, **kwargs).to(device) for _ in range(num_models)
        )
        (
            _,
            _,
            fn,
            weight_names,
            buffer_names,
        ) = make_functional_with_buffers_deprecated_v1(model_class(*args, **kwargs))
        weights, buffers = zip(
            *tuple(
                make_functional_with_buffers_deprecated_v1(model)[:2]
                for model in models
            )
        )
        weights = tuple(zip(*weights))
        weights = tuple(torch.stack(shards).detach() for shards in weights)
        buffers = tuple(zip(*buffers))
        buffers = tuple(torch.stack(shards).detach() for shards in buffers)
        return weights, buffers, fn, weight_names, buffer_names