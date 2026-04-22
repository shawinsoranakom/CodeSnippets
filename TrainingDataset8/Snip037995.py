def gather_metrics(
    name: str,
    func: None = None,
) -> Callable[[F], F]:
    ...