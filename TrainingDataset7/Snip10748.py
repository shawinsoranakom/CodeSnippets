def register_combinable_fields(lhs, connector, rhs, result):
    """
    Register combinable types:
        lhs <connector> rhs -> result
    e.g.
        register_combinable_fields(
            IntegerField, Combinable.ADD, FloatField, FloatField
        )
    """
    _connector_combinators[connector].append((lhs, rhs, result))