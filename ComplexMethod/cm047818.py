def set_state(self, state):
        ids_to_update = []
        for wo in self:
            if wo.state == state or 'done' in (wo.state, wo.production_state):
                continue
            if wo.state == 'progress':
                wo.button_pending()
            elif wo.state in ('done', 'cancel') and state == 'progress':
                wo.write({'state': 'ready'})  # Middle step to solve further conflict
            ids_to_update.append(wo.id)

        wo_to_update = self.browse(ids_to_update)
        if state == 'cancel':
            wo_to_update.action_cancel()
        elif state == 'done':
            wo_to_update.action_mark_as_done()
        elif state == 'progress':
            wo_to_update.button_start()
        else:
            wo_to_update.write({'state': state})