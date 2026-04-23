def _invoke(self, **kwargs):
        if self.check_if_canceled("Switch processing"):
            return

        for cond in self._param.conditions:
            if self.check_if_canceled("Switch processing"):
                return

            res = []
            for item in cond["items"]:
                if self.check_if_canceled("Switch processing"):
                    return

                if not item["cpn_id"]:
                    continue
                cpn_v = self._canvas.get_variable_value(item["cpn_id"])
                self.set_input_value(item["cpn_id"], cpn_v)
                operatee = item.get("value", "")
                if isinstance(cpn_v, numbers.Number):
                    operatee = float(operatee)
                res.append(self.process_operator(cpn_v, item["operator"], operatee))
                if cond["logical_operator"] != "and" and any(res):
                    self.set_output("next", [self._canvas.get_component_name(cpn_id) for cpn_id in cond["to"]])
                    self.set_output("_next", cond["to"])
                    return

            if all(res):
                self.set_output("next", [self._canvas.get_component_name(cpn_id) for cpn_id in cond["to"]])
                self.set_output("_next", cond["to"])
                return

        self.set_output("next", [self._canvas.get_component_name(cpn_id) for cpn_id in self._param.end_cpn_ids])
        self.set_output("_next", self._param.end_cpn_ids)