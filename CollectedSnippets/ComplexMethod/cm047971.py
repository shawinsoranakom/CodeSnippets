def _compute_filter_domain(self):
        for automation in self:
            field = (
                automation._get_trigger_specific_field()
                if automation.trigger not in ["on_create_or_write", *TIME_TRIGGERS]
                else False
            )
            if not field:
                automation.filter_domain = False
                continue

            # some triggers require a domain
            match automation.trigger:
                case 'on_state_set' | 'on_priority_set':
                    value = automation.trg_selection_field_id.value
                    automation.filter_domain = repr([(field.name, '=', value)]) if value else False
                case 'on_stage_set':
                    value = automation.trg_field_ref
                    automation.filter_domain = repr([(field.name, '=', value)]) if value else False
                case 'on_tag_set':
                    value = automation.trg_field_ref
                    automation.filter_domain = repr([(field.name, 'in', [value])]) if value else False
                case 'on_user_set':
                    automation.filter_domain = repr([(field.name, '!=', False)])
                case 'on_archive':
                    automation.filter_domain = repr([(field.name, '=', False)])
                case 'on_unarchive':
                    automation.filter_domain = repr([(field.name, '=', True)])