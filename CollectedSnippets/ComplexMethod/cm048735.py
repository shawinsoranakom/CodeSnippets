def _compute_parent_id(self):
        parent_id_vals_to_lines = defaultdict(list)
        for move, lines in self.grouped('move_id').items():
            if not move:
                parent_id_vals_to_lines[False].extend(lines._ids)
                continue
            last_section = False
            last_sub = False
            for line in move.line_ids.sorted('sequence'):
                value = False
                if line.display_type == 'line_section':
                    last_section = line
                    value = False
                    last_sub = False
                elif line.display_type == 'line_subsection':
                    value = last_section
                    last_sub = line
                elif line.display_type in {'line_note', 'product'}:
                    value = last_sub or last_section
                else:
                    value = False
                parent_id_vals_to_lines[value].append(line.id)

        for val, record_ids in parent_id_vals_to_lines.items():
            self.browse(record_ids).parent_id = val