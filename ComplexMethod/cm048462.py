def _set_date_deadline(self, new_deadline):
        # Handle the propagation of `date_deadline` fields (up and down stream - only update by up/downstream documents)
        already_propagate_ids = self.env.context.get('date_deadline_propagate_ids', set())
        already_propagate_ids.update(self.ids)
        self = self.with_context(date_deadline_propagate_ids=already_propagate_ids)
        for move in self:
            moves_to_update = (move.move_dest_ids | move.move_orig_ids)
            if move.date_deadline:
                delta = move.date_deadline - fields.Datetime.to_datetime(new_deadline)
            else:
                delta = 0
            for move_update in moves_to_update:
                if move_update.state in ('done', 'cancel'):
                    continue
                if move_update.id in already_propagate_ids:
                    continue
                if move_update.date_deadline and delta:
                    move_update.date_deadline -= delta
                elif not move_update.date_deadline or move_update.date_deadline != new_deadline:
                    move_update.date_deadline = new_deadline