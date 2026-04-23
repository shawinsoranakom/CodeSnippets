def from_row(cls, row, columns=None):
        if not columns:
            colnames = 'filename funcname name kind data'.split()
        else:
            colnames = list(columns)
            for i, column in enumerate(colnames):
                if column == 'file':
                    colnames[i] = 'filename'
                elif column == 'funcname':
                    colnames[i] = 'parent'
        if len(row) != len(set(colnames)):
            raise NotImplementedError(columns, row)
        kwargs = {}
        for column, value in zip(colnames, row):
            if column == 'filename':
                kwargs['file'] = FileInfo.from_raw(value)
            elif column == 'kind':
                kwargs['kind'] = KIND(value)
            elif column in cls._fields:
                kwargs[column] = value
            else:
                raise NotImplementedError(column)
        return cls(**kwargs)