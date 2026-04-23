def _get_signature(call: Callable[..., Any]) -> inspect.Signature:
    try:
        signature = inspect.signature(call, eval_str=True)
    except NameError:
        # Handle type annotations with if TYPE_CHECKING, not used by FastAPI
        # e.g. dependency return types
        if sys.version_info >= (3, 14):
            from annotationlib import Format

            signature = inspect.signature(call, annotation_format=Format.FORWARDREF)
        else:
            signature = inspect.signature(call)
    return signature