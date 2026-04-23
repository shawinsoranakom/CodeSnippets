def _zip_pad(self, lists: List[List[Any]], fill_value: Any) -> List[List[Any]]:
        """Zip lists, padding shorter ones with fill_value."""
        if not lists:
            return []
        lists = [lst for lst in lists if lst is not None]
        if not lists:
            return []
        max_len = max(len(lst) for lst in lists)
        result: List[List[Any]] = []
        for i in range(max_len):
            group: List[Any] = []
            for lst in lists:
                if i < len(lst):
                    group.append(lst[i])
                else:
                    group.append(fill_value)
            result.append(group)
        return result