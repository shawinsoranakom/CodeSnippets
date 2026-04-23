def write_line(self, values):
        """
        Write the values in the inner table.

        Args:
            values (`dict[str, float]`): The values to display.
        """
        if self.inner_table is None:
            self.inner_table = [list(values.keys()), list(values.values())]
        else:
            columns = self.inner_table[0]
            for key in values:
                if key not in columns:
                    columns.append(key)
            self.inner_table[0] = columns
            if len(self.inner_table) > 1:
                last_values = self.inner_table[-1]
                first_column = self.inner_table[0][0]
                if last_values[0] != values[first_column]:
                    # write new line
                    self.inner_table.append([values.get(c, "No Log") for c in columns])
                else:
                    # update last line
                    new_values = values
                    for c in columns:
                        if c not in new_values:
                            new_values[c] = last_values[columns.index(c)]
                    self.inner_table[-1] = [new_values[c] for c in columns]
            else:
                self.inner_table.append([values[c] for c in columns])