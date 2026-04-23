def get_doc_object(
    obj,
    what=None,
    doc=None,
    config=None,
    class_doc=ClassDoc,
    func_doc=FunctionDoc,
    obj_doc=ObjDoc,
):
    if what is None:
        if inspect.isclass(obj):
            what = "class"
        elif inspect.ismodule(obj):
            what = "module"
        elif isinstance(obj, Callable):
            what = "function"
        else:
            what = "object"
    if config is None:
        config = {}

    if what == "class":
        return class_doc(obj, func_doc=func_doc, doc=doc, config=config)
    elif what in ("function", "method"):
        return func_doc(obj, doc=doc, config=config)
    else:
        if doc is None:
            doc = pydoc.getdoc(obj)
        return obj_doc(obj, doc, config=config)