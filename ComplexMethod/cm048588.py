def _resequence_sections(self, sections, child_field, **kwargs):
        """Resequence the order content based on the new sequence order.

        :param list sections: A list of dictionaries containing move and target sections.
        :param str child_field: Field name of the order's lines (e.g., 'order_line').
        :param dict kwargs: Additional values given for inherited models.
        :return: A dictonary containing the new sequences of all the sections of order.
        :rtype: dict
        """
        lines = self[child_field].sorted('sequence')
        move_section, target_section = sections

        move_block = lines.filtered(
            lambda line: line.id == move_section['id']
            or line.parent_id.id == move_section['id'],
        )

        target_block = lines.filtered(
            lambda line: line.id == target_section['id']
            or line.parent_id.id == target_section['id'],
        )

        remaining_lines = lines - move_block
        insert_after = move_section['sequence'] < target_section['sequence']
        insert_index = len(remaining_lines)
        for idx, line in enumerate(remaining_lines):
            if line.id == (target_block[-1].id if insert_after else target_section['id']):
                insert_index = idx + 1 if insert_after else idx
                break

        reordered_lines = (
            remaining_lines[:insert_index] +
            move_block +
            remaining_lines[insert_index:]
        )

        sections = {}
        for sequence, line in enumerate(reordered_lines, start=1):
            line.sequence = sequence
            if line.display_type == 'line_section':
                sections[line.id] = sequence

        return sections