def _mark_dynamism(v, *other_vs):
            if not all(type(v) is type(other) for other in other_vs):
                raise ValueError(
                    "The following inputs were found to have differing types, "
                    f"so they cannot be marked as dynamic: {(v,) + other_vs}."
                )

            if isinstance(v, int) and not isinstance(v, bool):
                if all(other_v == v for other_v in other_vs):
                    return None
                else:
                    return Dim.DYNAMIC
            else:
                if not all(other_v == v for other_v in other_vs):
                    raise ValueError(
                        "The following inputs were found to have differing values, "
                        f"but they cannot be marked as dynamic: {(v,) + other_vs}."
                    )
                return None