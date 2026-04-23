def _lines(self, line_id=False, model_id=False, model=False, level=0, move_lines=None, **kw):
        final_vals = []
        lines = move_lines or []
        if model and line_id:
            move_line = self.env[model].browse(model_id)
            move_lines, is_used = self._get_linked_move_lines(move_line)
            if move_lines:
                lines = move_lines
            else:
                # Traceability in case of consumed in.
                lines = self._get_move_lines(move_line, line_id=line_id)
        for line in lines:
            unfoldable = False
            if line.consume_line_ids or (model != "stock.lot" and line.lot_id and self._get_move_lines(line)):
                unfoldable = True
            final_vals += self._make_dict_move(level, parent_id=line_id, move_line=line, unfoldable=unfoldable)
        return final_vals