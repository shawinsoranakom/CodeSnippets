def col_str(column, idx):
            # Index.__init__() guarantees that self.opclasses is the same
            # length as self.columns.
            col = "{} {}".format(self.quote_name(column), self.opclasses[idx])
            try:
                suffix = self.col_suffixes[idx]
                if suffix:
                    col = "{} {}".format(col, suffix)
            except IndexError:
                pass
            return col