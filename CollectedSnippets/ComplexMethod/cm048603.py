def should_delay(created_models, yet_to_be_created_models, model, field_name, field_val, parent_models=None):
                parent_models = (parent_models or []) + [model]
                field = self.env[model]._fields.get(field_name)
                if not field or not field.relational or field.comodel_name in created_models or isinstance(field_val, int):
                    return False
                field_yet_to_be_created = field.comodel_name in parent_models + yet_to_be_created_models
                if not isinstance(field_val, list | tuple):
                    return field_yet_to_be_created
                # Check recursively if there are subfields that should be delayed
                for element in field_val:
                    match element:
                        case Command.CREATE, _, dict() as values:
                            for subkey, subvalue in values.items():
                                if should_delay(created_models, yet_to_be_created_models, field.comodel_name, subkey, subvalue, parent_models):
                                    return True
                        case int() as command, *_ if command in tuple(Command):
                            if field_yet_to_be_created:
                                return True
                return False