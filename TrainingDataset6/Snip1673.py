def get_typed_return_annotation(call: Callable[..., Any]) -> Any:
    signature = _get_signature(call)
    unwrapped = inspect.unwrap(call)
    annotation = signature.return_annotation

    if annotation is inspect.Signature.empty:
        return None

    globalns = getattr(unwrapped, "__globals__", {})
    return get_typed_annotation(annotation, globalns)