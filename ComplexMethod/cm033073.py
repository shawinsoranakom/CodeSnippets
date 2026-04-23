def _get_filters(self, condition: dict) -> list[str]:
        filters: list[str] = []
        for k, v in condition.items():
            if not v:
                continue
            if k == "exists":
                filters.append(f"{v} IS NOT NULL")
            elif k == "must_not" and isinstance(v, dict) and "exists" in v:
                filters.append(f"{v.get('exists')} IS NULL")
            elif isinstance(v, list):
                values: list[str] = []
                for item in v:
                    values.append(get_value_str(item))
                value = ", ".join(values)
                filters.append(f"{k} IN ({value})")
            else:
                filters.append(f"{k} = {get_value_str(v)}")
        return filters