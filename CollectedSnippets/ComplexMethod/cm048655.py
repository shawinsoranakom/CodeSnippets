def _sync_dynamic_line_needed_values(self, values_list):
        res = {}
        for computed_needed in values_list:
            if computed_needed is False:
                continue  # there was an invalidation, let's hope nothing needed to be changed...
            for key, values in computed_needed.items():
                if key not in res:
                    res[key] = dict(values)
                else:
                    ignore = True
                    for fname in res[key]:
                        if self.env['account.move.line']._fields[fname].type == 'monetary':
                            res[key][fname] += values[fname]
                            if res[key][fname]:
                                ignore = False
                    if ignore:
                        del res[key]

        # Convert float values to their "ORM cache" one to prevent different rounding calculations
        for key, values in res.items():
            move_id = key.get('move_id')
            if not move_id:
                continue
            record = self.env['account.move'].browse(move_id)
            for fname, current_value in values.items():
                field = self.env['account.move.line']._fields[fname]
                if isinstance(current_value, float):
                    values[fname] = field.convert_to_cache(current_value, record)

        return res