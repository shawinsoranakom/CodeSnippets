def col_str(column, idx):
            col = self.quote_name(column)
            try:
                suffix = self.col_suffixes[idx]
                if suffix:
                    col = "{} {}".format(col, suffix)
            except IndexError:
                pass
            return col