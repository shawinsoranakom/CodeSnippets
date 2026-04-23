def get_test_param_values(
        cls,
        obj: t.Any,
        name: str,
        maybe_with_names: t.Iterable[str],
    ) -> tuple[t.Sequence[str], t.Iterable[t.Any], t.Callable[[object], str]]:
        value = getattr(obj, name)

        try:
            if inspect.ismethod(value):
                annot = get_type_hints(value, include_extras=True).get('return')
                value = value()
            else:
                annot = get_type_hints(obj, include_extras=True).get(name)
        except Exception as ex:
            raise Exception(f"failed getting type hints for {obj!r} {name!r}") from ex

        paramdesc = cls.get_paramdesc_from_hint(annot)

        if not paramdesc.names:
            paramdesc = dataclasses.replace(paramdesc, names=["value"])

        col_count = len(paramdesc.names)

        if col_count == 1:
            col_count = 0  # HACK: don't require a wrapper container around single-element rows

        maybe_with_names = set(maybe_with_names)

        # simulate ordered set with no-values dict; the output order is not important but must be consistent per-row; use the input data order for now
        matched_names = {n: None for n in paramdesc.names}

        if not matched_names:
            return [], [], str

        out_values = []

        # DTFIX-FUTURE: apply internal tagging/annotation to point at the source data row on test failure/error?
        for rownum, row in enumerate(value or []):
            if col_count:
                # validate column count and filter the args, returning them in `matched_names` order
                if len(row) != col_count:
                    raise ValueError(f"row {rownum} of {name!r} must contain exactly {col_count} value(s); found {len(row)}")

                out_values.append([argvalue for argname, argvalue in zip(paramdesc.names, row, strict=True) if argname in matched_names])
            else:
                # just return the entire row as "value"
                out_values.append([row])

        return list(matched_names), out_values, paramdesc.id_func