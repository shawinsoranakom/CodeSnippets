def _compute_crud_relations(self):
        """ Compute the crud_model_id and update_field_id fields.

        The crud_model_id is the model on which the action will create or update
        records. In the case of record creation, it is the same as the main model
        of the action. For record update, it will be the model linked to the last
        field in the update_path.
        This is only used for object_create and object_write actions.
        The update_field_id is the field at the end of the update_path that will
        be updated by the action - only used for object_write actions.
        """
        for action in self:
            if action.model_id and action.state in ('object_write', 'object_create', 'object_copy'):
                if action.state in ('object_create', 'object_copy'):
                    action.crud_model_id = action.model_id
                    action.update_field_id = False
                    action.update_path = False
                elif action.state == 'object_write':
                    if action.update_path:
                        # we need to traverse relations to find the target model and field
                        model, field = action._traverse_path()
                        action.crud_model_id = model
                        action.update_field_id = field
                        need_update_model = action.evaluation_type == 'value' and action.update_field_id and action.update_field_id.relation
                        action.update_related_model_id = action.env["ir.model"]._get_id(field.relation) if need_update_model else False
                    else:
                        action.crud_model_id = action.model_id
                        action.update_field_id = False
            else:
                action.crud_model_id = False
                action.update_field_id = False
                action.update_path = False