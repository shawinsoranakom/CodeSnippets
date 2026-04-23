def _parse_columns(cls, columns):
        colnames = {}  # {requested -> actual}
        columns = list(columns or cls.FIELDS)
        datacolumns = []
        for i, colname in enumerate(columns):
            if colname == 'file':
                columns[i] = 'filename'
                colnames['file'] = 'filename'
            elif colname == 'lno':
                columns[i] = 'line'
                colnames['lno'] = 'line'
            elif colname in ('filename', 'line'):
                colnames[colname] = colname
            elif colname == 'data':
                datacolumns.append(colname)
                colnames[colname] = None
            elif colname in cls.FIELDS or colname == 'kind':
                colnames[colname] = colname
            else:
                datacolumns.append(colname)
                colnames[colname] = None
        return columns, datacolumns, colnames