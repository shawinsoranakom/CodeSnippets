def write_cell(self, row, column, cell_value):
        cell_style = self.base_style

        if isinstance(cell_value, bytes):
            try:
                # because xlsx uses raw export, we can get a bytes object
                # here. xlsxwriter does not support bytes values in Python 3 ->
                # assume this is base64 and decode to a string, if this
                # fails note that you can't export
                cell_value = cell_value.decode()
            except UnicodeDecodeError:
                raise UserError(request.env._("Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.", self.columns_headers[column])) from None
        elif isinstance(cell_value, (list, tuple, dict)):
            cell_value = str(cell_value)

        if isinstance(cell_value, str):
            if len(cell_value) > self.worksheet.xls_strmax:
                cell_value = request.env._("The content of this cell is too long for an XLSX file (more than %s characters). Please use the CSV format for this export.", self.worksheet.xls_strmax)
            else:
                cell_value = cell_value.replace("\r", " ")
        elif isinstance(cell_value, datetime.datetime):
            cell_style = self.datetime_style
        elif isinstance(cell_value, datetime.date):
            cell_style = self.date_style
        elif isinstance(cell_value, float):
            field = self.fields[column]
            cell_style = self.monetary_style if field['type'] == 'monetary' else self.float_style
        self.write(row, column, cell_value, cell_style)