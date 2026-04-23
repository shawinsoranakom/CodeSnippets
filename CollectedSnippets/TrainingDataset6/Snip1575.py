def is_pydantic_v1_model_instance(obj: Any) -> bool:
    # TODO: remove this function once the required version of Pydantic fully
    # removes pydantic.v1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            from pydantic import v1
    except ImportError:  # pragma: no cover
        return False
    return isinstance(obj, v1.BaseModel)