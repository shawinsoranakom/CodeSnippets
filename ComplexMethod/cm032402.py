def _split(self, line:str|None = None):
        if self.check_if_canceled("StringTransform split processing"):
            return

        var = self._canvas.get_variable_value(self._param.split_ref) if not line else line
        if not var:
            var = ""
        assert isinstance(var, str), "The input variable is not a string: {}".format(type(var))
        self.set_input_value(self._param.split_ref, var)

        res = []
        for i,s in enumerate(re.split(r"(%s)"%("|".join([re.escape(d) for d in self._param.delimiters])), var, flags=re.DOTALL)):
            if i % 2 == 1:
                continue
            res.append(s)
        self.set_output("result", res)