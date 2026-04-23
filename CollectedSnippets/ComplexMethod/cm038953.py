def collect_timings(
    op: IrOp, shape_configs: list[dict], cfg: BenchConfig
) -> tuple[list[str], list[str], dict[str, dict[str, float]]]:
    def fmt(v) -> str:
        return str(v).split(".")[-1] if isinstance(v, torch.dtype) else str(v)

    case_names = [
        "_".join(f"{k}={fmt(v)}" for k, v in kwargs.items()) for kwargs in shape_configs
    ]
    providers = [n for n, impl in op.impls.items() if impl.supported]

    results: dict[str, dict[str, float]] = {c: {} for c in case_names}
    for provider in providers:
        impl = op.impls[provider]
        desc = f"{op.name} / {provider}"
        for case_name, kwargs in tqdm(
            zip(case_names, shape_configs),
            desc=desc,
            total=len(case_names),
            unit=" cases",
        ):
            args = op.generate_inputs(**kwargs)
            if impl.supports_args(*args):
                results[case_name][provider] = _bench_one(impl.impl_fn, args, cfg)
            else:
                results[case_name][provider] = float("nan")

    return case_names, providers, results