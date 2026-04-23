def depart_table(self, node):
        self.compact_p = self.context.pop()
        self._table_row_indices.pop()
        self.body.append("</table>\n")