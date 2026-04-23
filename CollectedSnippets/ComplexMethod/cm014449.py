def _collate_helper(conversion, item):
    # TODO(VitalyFedyunin): Verify that item is any sort of batch
    if len(item.items) > 1:
        # TODO(VitalyFedyunin): Compact all batch dataframes into one
        raise RuntimeError("Only supports one DataFrame per batch")
    df = item[0]
    columns_name = df_wrapper.get_columns(df)
    tuple_names: list = []
    tuple_values: list = []

    for name in conversion:
        if name not in columns_name:
            raise RuntimeError("Conversion keys mismatch")

    for name in columns_name:
        if name in conversion:
            if not callable(conversion[name]):
                raise RuntimeError(
                    "Collate (DF)DataPipe requires callable as dict values"
                )
            collation_fn = conversion[name]
        else:
            # TODO(VitalyFedyunin): Add default collation into df_wrapper
            try:
                import torcharrow.pytorch as tap  # type: ignore[import]

                collation_fn = tap.rec.Default()
            except Exception as e:
                raise RuntimeError(
                    "unable to import default collation function from the TorchArrow"
                ) from e

        tuple_names.append(str(name))
        value = collation_fn(df[name])
        tuple_values.append(value)

    # TODO(VitalyFedyunin): We can dynamically extract types from the tuple_values here
    # TODO(VitalyFedyunin): Instead of ignoring mypy error, make sure tuple_names is not empty
    tpl_cls = namedtuple("CollateResult", tuple_names)  # type: ignore[misc]
    tuple = tpl_cls(*tuple_values)
    return tuple