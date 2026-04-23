def update_reference(self, idx: int, operation: str, field: str, value: Any, ref_idx=None) -> None:
        while len(self.list) <= idx:
            self.list.append({})

        if operation == "append" or operation == "add":
            if not isinstance(self.list[idx].get(field, None), list):
                self.list[idx][field] = []
            if isinstance(value, list):
                self.list[idx][field].extend(value)
            else:
                self.list[idx][field].append(value)

        if operation == "replace" and ref_idx is not None:
            if field == "refs" and not isinstance(self.list[idx].get(field, None), list):
                self.list[idx][field] = []

            if isinstance(self.list[idx][field], list):
                if len(self.list[idx][field]) <= ref_idx:
                    self.list[idx][field].append(value)
                else:
                    self.list[idx][field][ref_idx] = value
            else:
                self.list[idx][field] = value