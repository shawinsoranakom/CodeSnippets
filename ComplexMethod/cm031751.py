def join_tables(self, rows_a: Rows, rows_b: Rows) -> tuple[Columns, Rows]:
        ncols = len(self.columns)

        default = ("",) * (ncols - 1)
        data_a = {x[0]: x[1:] for x in rows_a}
        data_b = {x[0]: x[1:] for x in rows_b}

        if len(data_a) != len(rows_a) or len(data_b) != len(rows_b):
            raise ValueError("Duplicate keys")

        # To preserve ordering, use A's keys as is and then add any in B that
        # aren't in A
        keys = list(data_a.keys()) + [k for k in data_b.keys() if k not in data_a]
        rows = [
            self.join_row(k, data_a.get(k, default), data_b.get(k, default))
            for k in keys
        ]
        if self.join_mode in (JoinMode.CHANGE, JoinMode.CHANGE_ONE_COLUMN):
            rows.sort(key=lambda row: abs(float(row[-1])), reverse=True)

        columns = self.join_columns(self.columns)
        return columns, rows