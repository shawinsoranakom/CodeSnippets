def _value_or_dg(value: Value, dg: DG) -> Value:
    # This overload definition technically overlaps with the one above (Value
    # contains Type[NoValue]), and since the return types are conflicting,
    # mypy complains. Hence, the ignore-comment above. But, in practice, since
    # the overload above is more specific, and is matched first, there is no
    # actual overlap. The `Value` type here is thus narrowed to the cases
    # where value is neither None nor NoValue.

    # The ignore-comment should thus be fine.
    ...