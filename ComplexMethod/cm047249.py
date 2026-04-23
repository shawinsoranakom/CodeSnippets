def _interpolation_dict():
            now = range_date = effective_date = datetime.now(self.env.tz)
            if date or self.env.context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self.env.context.get('ir_sequence_date'))
            if date_range or self.env.context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self.env.context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S',
                'isoyear': '%G', 'isoy': '%g', 'isoweek': '%V',
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            return res