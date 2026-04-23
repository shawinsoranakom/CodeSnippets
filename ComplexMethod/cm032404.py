def _invoke(self, **kwargs):
        self.input_objects=[]
        inputs = getattr(self._param, "query", None)
        self.inputs = self._canvas.get_variable_value(inputs)
        if not isinstance(self.inputs, list):
            raise TypeError("The input of List Operations should be an array.")
        self.set_input_value(inputs, self.inputs)
        if self._param.operations == "topN":
            self._topN()
        elif self._param.operations == "head":
            self._head()
        elif self._param.operations == "tail":
            self._tail()
        elif self._param.operations == "filter":
            self._filter()
        elif self._param.operations == "sort":
            self._sort()
        elif self._param.operations == "drop_duplicates":
            self._drop_duplicates()