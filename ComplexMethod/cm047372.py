def _compute_is_visible(self):
        active_id = self.env.context.get("active_id", False)
        if not active_id:
            self.is_visible = False
            return
        domain_id = [("id", "=", active_id)]
        for parent_res_model, records in self.grouped('parent_res_model').items():
            active_model_record = self.env[parent_res_model].search(domain_id, order='id')
            for record in records:
                action_groups = record.groups_ids
                is_valid_method = not record.python_method or hasattr(self.env[parent_res_model], record.python_method)
                if is_valid_method and (not action_groups or (action_groups & self.env.user.all_group_ids)):
                    domain_model = literal_eval(record.domain or '[]')
                    record.is_visible = (
                        record.parent_res_id in (False, self.env.context.get('active_id', False))
                        and record.user_id.id in (False, self.env.uid)
                        and active_model_record.filtered_domain(domain_model)
                    )
                else:
                    record.is_visible = False