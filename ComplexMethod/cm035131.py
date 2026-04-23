def get_number_format(self):
        if "TYPE_CURRENCY" in self.element.get("class", "").split():
            return FORMAT_CURRENCY_USD_SIMPLE
        if "TYPE_INTEGER" in self.element.get("class", "").split():
            return "#,##0"
        if "TYPE_PERCENTAGE" in self.element.get("class", "").split():
            return FORMAT_PERCENTAGE
        if "TYPE_DATE" in self.element.get("class", "").split():
            return FORMAT_DATE_MMDDYYYY
        if self.data_type() == cell.TYPE_NUMERIC:
            try:
                int(self.value)
            except ValueError:
                return "#,##0.##"
            else:
                return "#,##0"