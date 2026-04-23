def _compute_move_finished_ids(self):
        production_with_move_finished_ids_to_unlink_ids = OrderedSet()
        ignored_mo_ids = self.env.context.get('ignore_mo_ids', [])
        for production in self:
            if production.id in ignored_mo_ids:
                continue
            if production.state != 'draft':
                updated_values = {}
                if production.date_finished:
                    updated_values['date'] = production.date_finished
                if production.date_deadline:
                    updated_values['date_deadline'] = production.date_deadline
                if 'date' in updated_values or 'date_deadline' in updated_values:
                    production.move_finished_ids = [
                        Command.update(m.id, updated_values) for m in production.move_finished_ids
                        if any(
                            updated_values.get(field) and m[field] != updated_values[field]
                            for field in ('date', 'date_deadline')
                        )
                    ]
                continue
            production_with_move_finished_ids_to_unlink_ids.add(production.id)

        production_with_move_finished_ids_to_unlink = self.browse(production_with_move_finished_ids_to_unlink_ids)

        # delete to remove existing moves from database and clear to remove new records
        production_with_move_finished_ids_to_unlink.move_finished_ids = [Command.delete(m) for m in production_with_move_finished_ids_to_unlink.move_finished_ids.ids]
        production_with_move_finished_ids_to_unlink.move_finished_ids = [Command.clear()]

        for production in production_with_move_finished_ids_to_unlink:
            if production.product_id:
                production._create_update_move_finished()
            else:
                production.move_finished_ids = [
                    Command.delete(move.id) for move in production.move_finished_ids if move.bom_line_id
                ]