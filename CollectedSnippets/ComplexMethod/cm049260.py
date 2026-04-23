def from_data(self, fields, columns_headers, rows):
        fp = io.StringIO()
        writer = csv.writer(fp, quoting=1)

        writer.writerow(columns_headers)

        for data in rows:
            row = []
            for d in data:
                if d is None or d is False:
                    d = ''
                elif isinstance(d, bytes):
                    d = d.decode()
                # Spreadsheet apps tend to detect formulas on leading =, + and -
                if isinstance(d, str) and d.startswith(('=', '-', '+')):
                    d = "'" + d

                row.append(d)
            writer.writerow(row)

        return fp.getvalue()