def match_rule(self, obj, rule):
        key = rule.get("key")
        op = (rule.get("operator") or "equals").lower()
        target = self.norm(rule.get("value"))
        target = self._canvas.get_value_with_variable(target) or target
        if key not in obj:
            return False
        val = obj.get(key, None)
        v = self.norm(val)
        if op == "=":
            return v == target
        if op == "≠":
            return v != target
        if op == "contains":
            return target in v
        if op == "start with":
            return v.startswith(target)
        if op == "end with":
            return v.endswith(target)
        return False