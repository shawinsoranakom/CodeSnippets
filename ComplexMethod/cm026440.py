def convert(result: Any) -> Any | None:
        if check_result_for_none(result, **kwargs):
            return None

        # items may be mutable based on another template field. Always
        # perform this check when the items come from an configured
        # attribute.
        if isinstance(items, str):
            _items = getattr(entity, items)
        else:
            _items = items

        if _items is None or (len(_items) == 0):
            if items_attribute:
                log_validation_result_error(
                    entity,
                    attribute,
                    result,
                    f"{items_attribute} is empty",
                )

            return None

        if result not in _items:
            log_validation_result_error(
                entity,
                attribute,
                result,
                tuple(str(v) for v in _items),
            )
            return None

        return result