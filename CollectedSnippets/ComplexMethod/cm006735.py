def _is_cleared(val: Any) -> bool:
                return (
                    not val
                    or (
                        isinstance(val, list)
                        and (len(val) == 0 or (len(val) > 0 and isinstance(val[0], dict) and not val[0].get("name")))
                    )
                    or (isinstance(val, str) and val in ("", "disabled", "placeholder"))
                )