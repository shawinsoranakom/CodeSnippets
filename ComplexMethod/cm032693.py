def _be_children(self, obj: dict, keyset: set):
        if isinstance(obj, str):
            obj = [obj]
        if isinstance(obj, list):
            keyset.update(obj)
            obj = [re.sub(r"\*+", "", i) for i in obj]
            return [{"id": i, "children": []} for i in obj if i]
        arr = []
        for k, v in obj.items():
            k = self._key(k)
            if k and k not in keyset:
                keyset.add(k)
                arr.append(
                    {
                        "id": k,
                        "children": self._be_children(v, keyset)
                    }
                )
        return arr