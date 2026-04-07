def visit_table(self, node):
        self.context.append(self.compact_p)
        self.compact_p = True
        # Needed by Sphinx.
        self._table_row_indices.append(0)
        self.body.append(self.starttag(node, "table", CLASS="docutils"))