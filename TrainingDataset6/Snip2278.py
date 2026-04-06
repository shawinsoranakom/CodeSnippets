def broken_dep() -> Any:
    yield "s"
    raise ValueError("Broken after yield")