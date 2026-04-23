def _operate(self,variable,operator,parameter):
        if operator == "overwrite":
            return self._overwrite(parameter)
        elif operator == "clear":
            return self._clear(variable)
        elif operator == "set":
            return self._set(variable,parameter)
        elif operator == "append":
            return self._append(variable,parameter)
        elif operator == "extend":
            return self._extend(variable,parameter)
        elif operator == "remove_first":
            return self._remove_first(variable)
        elif operator == "remove_last":
            return self._remove_last(variable)
        elif operator == "+=":
            return self._add(variable,parameter)
        elif operator == "-=":
            return self._subtract(variable,parameter)
        elif operator == "*=":
            return self._multiply(variable,parameter)
        elif operator == "/=":
            return self._divide(variable,parameter)
        else:
            return