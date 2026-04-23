def delay(all_data):
            """Defer writing some relations if the related records don't exist yet."""

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

            created_models = set()
            while all_data:
                (model, data), *all_data = all_data
                yet_to_be_created_models = [model for model, _data in all_data if _data]
                to_delay = defaultdict(dict)
                for xml_id, vals in data.items():
                    to_be_removed = []
                    for field_name, field_val in vals.items():
                        if should_delay(created_models, yet_to_be_created_models, model, field_name, field_val):
                            # Default repartition lines will be created when we create account.tax
                            # If we delay the creation of repartition_line_ids, then we must get rid of the defaults
                            if (
                                model == 'account.tax' and 'repartition_line_ids' in field_name
                                and not self.ref(xml_id, raise_if_not_found=False)
                                and all(
                                    isinstance(x, tuple | list) and len(x)
                                    and isinstance(x[0], Command | int) for x in field_val
                                )
                            ):
                                field_val = [Command.clear()] + field_val
                            to_be_removed.append(field_name)
                            to_delay[xml_id][field_name] = field_val
                    for field_name in to_be_removed:
                        del vals[field_name]
                if any(to_delay.values()):
                    all_data.append((model, to_delay))
                yield model, data
                created_models.add(model)