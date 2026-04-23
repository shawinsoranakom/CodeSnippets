def _render_data_row(cls, fmt, data, extra, colnames):
        if fmt != 'row':
            raise NotImplementedError
        datarow = cls._data_as_row(data, extra, colnames)
        unresolved = [c for c, v in datarow.items() if v is None]
        if unresolved:
            raise NotImplementedError(unresolved)
        for colname, value in datarow.items():
            if type(value) != str:
                if colname == 'kind':
                    datarow[colname] = value.value
                else:
                    datarow[colname] = str(value)
        return datarow