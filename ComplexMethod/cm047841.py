def _get_linked_move_lines(self, move_line):
        move_lines, is_used = super()._get_linked_move_lines(move_line)
        if not move_lines:
            move_lines = (move_line.move_id.consume_unbuild_id and move_line.produce_line_ids) or (move_line.move_id.production_id and move_line.consume_line_ids)
        if not is_used:
            is_used = (move_line.move_id.unbuild_id and move_line.consume_line_ids) or (move_line.move_id.raw_material_production_id and move_line.produce_line_ids)
        return move_lines, is_used