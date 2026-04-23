def get_input_form(self) -> dict[str, dict]:
        res = {}
        for item in self._param.variables or []:
            if not isinstance(item, dict):
                continue
            ref = (item.get("ref") or "").strip()
            if not ref or ref in res:
                continue

            elements = self.get_input_elements_from_text("{" + ref + "}")
            element = elements.get(ref, {})
            res[ref] = {
                "type": "line",
                "name": element.get("name") or item.get("key") or ref,
            }
        return res