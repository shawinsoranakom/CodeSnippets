def request_from_dict(d: dict[str, Any], *, spider: Spider | None = None) -> Request:
    """Create a :class:`~scrapy.Request` object from a dict.

    If a spider is given, it will try to resolve the callbacks looking at the
    spider for methods with the same name.
    """
    request_cls: type[Request] = load_object(d["_class"]) if "_class" in d else Request
    kwargs = {key: value for key, value in d.items() if key in request_cls.attributes}
    if d.get("callback") and spider:
        kwargs["callback"] = _get_method(spider, d["callback"])
    if d.get("errback") and spider:
        kwargs["errback"] = _get_method(spider, d["errback"])
    return request_cls(**kwargs)