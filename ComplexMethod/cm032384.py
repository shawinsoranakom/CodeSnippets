def _invoke(self, **kwargs):
        self.input_objects=[]
        inputs = getattr(self._param, "query", None)
        if not isinstance(inputs, (list, tuple)):
            inputs = [inputs]
        for input_ref in inputs:
            input_object=self._canvas.get_variable_value(input_ref)
            self.set_input_value(input_ref, input_object)
            if input_object is None:
                continue
            if isinstance(input_object,dict):
                self.input_objects.append(input_object)
            elif isinstance(input_object,list):
                self.input_objects.extend(x for x in input_object if isinstance(x, dict))
            else:
                continue
        if self._param.operations == "select_keys":
            self._select_keys()
        elif self._param.operations == "recursive_eval":
            self._literal_eval()
        elif self._param.operations == "combine":
            self._combine()
        elif self._param.operations == "filter_values":
            self._filter_values()
        elif self._param.operations == "append_or_update":
            self._append_or_update()
        elif self._param.operations == "remove_keys":
            self._remove_keys()
        else:
            self._rename_keys()