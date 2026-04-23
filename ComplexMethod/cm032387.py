def _append_or_update(self):
        results=[]
        updates = getattr(self._param, "updates", []) or [] 
        for obj in self.input_objects:
            new_obj = dict(obj)
            for item in updates:
                if not isinstance(item, dict):
                    continue
                k = (item.get("key") or "").strip()
                if not k:
                    continue
                new_obj[k] = self._canvas.get_value_with_variable(item.get("value")) or item.get("value")
            results.append(new_obj)
        self.set_output("result", results)