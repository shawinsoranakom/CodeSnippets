def render_rowdata(self, columns=None):
        columns, datacolumns, colnames = self._parse_columns(columns)
        def data_as_row(data, ext, cols):
            return self._render_data_row('row', data, ext, cols)
        rowdata = self._as_row(colnames, datacolumns, data_as_row)
        for column, value in rowdata.items():
            colname = colnames.get(column)
            if not colname:
                continue
            if column == 'kind':
                value = value.value
            else:
                if column == 'parent':
                    if self.parent:
                        value = f'({self.parent.kind.value} {self.parent.name})'
                if not value:
                    value = '-'
                elif type(value) is VarType:
                    value = repr(str(value))
                else:
                    value = str(value)
            rowdata[column] = value
        return rowdata