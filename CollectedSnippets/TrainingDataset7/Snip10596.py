def make_foreign_order_accessors(model, related_model):
    setattr(
        related_model,
        "get_%s_order" % model.__name__.lower(),
        partialmethod(method_get_order, model),
    )
    setattr(
        related_model,
        "set_%s_order" % model.__name__.lower(),
        partialmethod(method_set_order, model),
    )