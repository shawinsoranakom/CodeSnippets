def compare(row_value: Any, op: str, comp_value: str) -> bool:
            # Try numeric comparison
            try:
                row_num = float(row_value)
                comp_num = float(comp_value)
                if op == "eq":
                    return row_num == comp_num
                elif op == "ne":
                    return row_num != comp_num
                elif op == "gt":
                    return row_num > comp_num
                elif op == "lt":
                    return row_num < comp_num
                elif op == "gte":
                    return row_num >= comp_num
                elif op == "lte":
                    return row_num <= comp_num
            except (ValueError, TypeError):
                pass

            # String comparison
            row_str = str(row_value).lower()
            comp_str = comp_value.lower()

            if op == "eq":
                return row_str == comp_str
            elif op == "ne":
                return row_str != comp_str
            elif op == "contains":
                return comp_str in row_str
            elif op in ("gt", "lt", "gte", "lte"):
                # String comparison for non-numeric
                if op == "gt":
                    return row_str > comp_str
                elif op == "lt":
                    return row_str < comp_str
                elif op == "gte":
                    return row_str >= comp_str
                elif op == "lte":
                    return row_str <= comp_str

            return False