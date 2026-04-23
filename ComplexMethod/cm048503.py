def _compute_preview_moves(self):
        """Reduce the computed new_values to a smaller set to display in the preview."""
        for record in self:
            new_values = sorted(json.loads(record.new_values).values(), key=lambda x: x['server-date'], reverse=True)
            changeLines = []
            in_elipsis = 0
            previous_line = None
            for i, line in enumerate(new_values):
                if i < 3 or i == len(new_values) - 1 or line['new_by_name'] != line['new_by_date'] \
                 or (self.sequence_number_reset == 'year' and line['server-date'][0:4] != previous_line['server-date'][0:4])\
                 or (self.sequence_number_reset == 'year_range' and line['server-year-start-date'][0:4] != previous_line['server-year-start-date'][0:4])\
                 or (self.sequence_number_reset == 'month' and line['server-date'][0:7] != previous_line['server-date'][0:7]):
                    if in_elipsis:
                        changeLines.append({
                            'id': 'other_' + str(line['id']),
                            'current_name': _('... (%(nb_of_values)s other)', nb_of_values=in_elipsis),
                            'new_by_name': '...',
                            'new_by_date': '...',
                            'date': '...',
                        })
                        in_elipsis = 0
                    changeLines.append(line)
                else:
                    in_elipsis += 1
                previous_line = line

            record.preview_moves = json.dumps({
                'ordering': record.ordering,
                'changeLines': changeLines,
            })