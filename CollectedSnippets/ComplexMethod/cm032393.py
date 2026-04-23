def _invoke(self, **kwargs):
        if self.check_if_canceled("Loop processing"):
            return

        for item in self._param.loop_variables:
            if any([not item.get("variable"), not item.get("input_mode"), not item.get("value"),not item.get("type")]):
                assert "Loop Variable is not complete."
            if item["input_mode"]=="variable":
                self.set_output(item["variable"],self._canvas.get_variable_value(item["value"]))
            elif item["input_mode"]=="constant":
                self.set_output(item["variable"],item["value"])
            else:
                if item["type"] == "number":
                    self.set_output(item["variable"], 0)
                elif item["type"] == "string":
                    self.set_output(item["variable"], "")
                elif item["type"] == "boolean":
                    self.set_output(item["variable"], False)
                elif item["type"].startswith("object"):
                    self.set_output(item["variable"], {})
                elif item["type"].startswith("array"):
                    self.set_output(item["variable"], [])
                else:
                    self.set_output(item["variable"], "")