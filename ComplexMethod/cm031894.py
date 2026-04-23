def _as_row(self, colnames, datacolumns, data_as_row):
        try:
            data = data_as_row(self.data, self._extra, datacolumns)
        except NotImplementedError:
            data = None
        row = data or {}
        for column, colname in colnames.items():
            if colname == 'filename':
                value = self.file.filename if self.file else None
            elif colname == 'line':
                value = self.file.lno if self.file else None
            elif colname is None:
                value = getattr(self, column, None)
            else:
                value = getattr(self, colname, None)
            row.setdefault(column, value)
        return row