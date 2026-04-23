def _rename_keys(self):
        results = []
        rename_pairs = getattr(self._param, "rename_keys", []) or []

        for obj in (self.input_objects or []):
            new_obj = dict(obj)
            for pair in rename_pairs:
                if not isinstance(pair, dict):
                    continue
                old = (pair.get("old_key") or "").strip()
                new = (pair.get("new_key") or "").strip()
                if not old or not new or old == new:
                    continue
                if old in new_obj:
                    new_obj[new] = new_obj.pop(old)
            results.append(new_obj)
        self.set_output("result", results)