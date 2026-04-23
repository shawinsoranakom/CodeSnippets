def _is_recompute(self):
        """When an activity is set on update of a record,
        update might be triggered many times by recomputes.
        When need to know it to skip these steps.
        Except if the computed field is supposed to trigger the action
        """
        records = self.env[self.model_name].browse(
            self.env.context.get('active_ids', self.env.context.get('active_id')))
        old_values = self.env.context.get('old_values')
        if old_values:
            domain_post = self.env.context.get('domain_post')
            tracked_fields = []
            if domain_post:
                for leaf in domain_post:
                    if isinstance(leaf, (tuple, list)):
                        tracked_fields.append(leaf[0])
            fields_to_check = [field for record, field_names in old_values.items() for field in field_names if field not in tracked_fields]
            if fields_to_check:
                field = records._fields[fields_to_check[0]]
                # Pick an arbitrary field; if it is marked to be recomputed,
                # it means we are in an extraneous write triggered by the recompute.
                # In this case, we should not create a new activity.
                if records & self.env.records_to_compute(field):
                    return True
        return False