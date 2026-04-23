def _add_followers(self, partners):
        self.ensure_one()
        self.message_subscribe(partners.ids)

        dict_tasks_per_partner = {}
        dict_partner_ids_to_subscribe_per_partner = {}
        for task in self.task_ids:
            if task.partner_id in dict_tasks_per_partner:
                dict_tasks_per_partner[task.partner_id] |= task
            else:
                partner_ids_to_subscribe = [
                    partner.id for partner in partners
                    if partner == task.partner_id or partner in task.partner_id.child_ids
                ]
                if partner_ids_to_subscribe:
                    dict_tasks_per_partner[task.partner_id] = task
                    dict_partner_ids_to_subscribe_per_partner[task.partner_id] = partner_ids_to_subscribe
        for partner, tasks in dict_tasks_per_partner.items():
            tasks.message_subscribe(dict_partner_ids_to_subscribe_per_partner[partner])