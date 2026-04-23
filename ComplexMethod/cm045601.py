def _convert_from_json(name: str, col: pw.ColumnExpression):
        _type = dt.unoptionalize(typehints[name])
        is_optional = isinstance(typehints[name], dt.Optional)
        result: pw.ColumnExpression

        def _optional(
            col: pw.ColumnExpression,
            op: Callable[[pw.ColumnExpression], pw.ColumnExpression],
        ) -> pw.ColumnExpression:
            if is_optional:
                return pw.if_else(col == pw.Json.NULL, None, op(col))
            else:
                return op(col)

        match _type:
            case dt.JSON:
                result = col
            case dt.BOOL:
                result = col.as_bool()
            case dt.FLOAT:
                result = col.as_float()
            case dt.INT:
                result = col.as_int()
            case dt.STR:
                result = col.as_str()
            case dt.DATE_TIME_NAIVE:
                result = _optional(
                    col,
                    lambda col: pw.unwrap(col.as_str()).dt.strptime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                )
            case dt.DATE_TIME_UTC:
                result = _optional(
                    col,
                    lambda col: pw.unwrap(col.as_str()).dt.strptime(
                        "%Y-%m-%dT%H:%M:%S.%f%z"
                    ),
                )
            case dt.DURATION:
                result = _optional(
                    col, lambda col: pw.unwrap(col.as_int()).dt.to_duration("ns")
                )
            case _:
                raise TypeError(
                    f"Unsupported conversion from pw.Json to {typehints[name]}"
                )

        return result if is_optional else pw.unwrap(result)