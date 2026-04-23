def write(self, vals):
        new_implementation = vals.get('implementation')
        for seq in self:
            # 4 cases: we test the previous impl. against the new one.
            i = vals.get('number_increment', seq.number_increment)
            n = vals.get('number_next', seq.number_next)
            if seq.implementation == 'standard':
                if new_implementation in ('standard', None):
                    # Implementation has NOT changed.
                    # Only change sequence if really requested.
                    if vals.get('number_next'):
                        _alter_sequence(self.env.cr, "ir_sequence_%03d" % seq.id, number_next=n)
                    if seq.number_increment != i:
                        _alter_sequence(self.env.cr, "ir_sequence_%03d" % seq.id, number_increment=i)
                        seq.date_range_ids._alter_sequence(number_increment=i)
                else:
                    _drop_sequences(self.env.cr, ["ir_sequence_%03d" % seq.id])
                    for sub_seq in seq.date_range_ids:
                        _drop_sequences(self.env.cr, ["ir_sequence_%03d_%03d" % (seq.id, sub_seq.id)])
            else:
                if new_implementation in ('no_gap', None):
                    pass
                else:
                    _create_sequence(self.env.cr, "ir_sequence_%03d" % seq.id, i, n)
                    for sub_seq in seq.date_range_ids:
                        _create_sequence(self.env.cr, "ir_sequence_%03d_%03d" % (seq.id, sub_seq.id), i, n)
        res = super().write(vals)
        # DLE P179
        self.flush_model(vals.keys())
        return res