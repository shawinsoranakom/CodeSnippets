def _load_data(self, data):
        """Load all the data linked to the template into the database.

        The data can contain translation values (i.e. `name@fr_FR` to translate the name in French)
        An xml_id that doesn't contain a `.` will be treated as being linked to `account` and prefixed
        with the company's id (i.e. `cash` is interpreted as `account.1_cash` if the company's id is 1)

        :param data: Basically all the final data of records to create/update for the chart
                     of accounts. It is a mapping {model: {xml_id: values}}.
        :type data: dict[str, dict[(str, int), dict]]
        """
        def deref_values(values, model):
            """Replace xml_id references by database ids in all provided values.

            This allows to define all the data before the records even exist in the database.
            """
            fields = ((model._fields[k], k, v) for k, v in values.items() if k in model._fields)
            failed_fields = []
            for field, fname, value in fields:
                if not value:
                    values[fname] = False
                elif isinstance(value, str) and (
                    field.type == 'many2one'
                    or (field.type in ('integer', 'many2one_reference') and not value.isdigit())
                ):
                    try:
                        values[fname] = self.ref(value).id if value not in ('', 'False', 'None') else False
                    except ValueError:
                        if model._name == 'res.company':
                            # Try a fallback on the company when reloading/loading on a branch
                            values[fname] = self.env.company[fname] or self.env.company.root_id[fname] or False
                        else:
                            _logger.warning("Failed when trying to recover %s for field=%s", value, field)
                            failed_fields.append(fname)
                            values[fname] = False
                elif field.type in ('one2many', 'many2many') and isinstance(value[0], (list, tuple)):
                    for i, (command, _id, *last_part) in enumerate(value):
                        if last_part:
                            last_part = last_part[0]
                        # (0, 0, {'test': 'account.ref_name'}) -> Command.Create({'test': 13})
                        if command in (Command.CREATE, Command.UPDATE):
                            deref_values(last_part, self.env[field.comodel_name])
                        # (6, 0, ['account.ref_name']) -> Command.Set([13])
                        elif command == Command.SET:
                            for subvalue_idx, subvalue in enumerate(last_part):
                                if isinstance(subvalue, str):
                                    last_part[subvalue_idx] = self.ref(subvalue).id
                        elif command == Command.LINK and isinstance(_id, str):
                            value[i] = Command.link(self.ref(_id).id)
                elif field.type in ('one2many', 'many2many') and isinstance(value, str):
                    values[fname] = [Command.set([
                        self.ref(v).id
                        for v in value.split(',')
                        if v
                    ])]
            for fname in failed_fields:
                del values[fname]
            return values

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

        created_records = {}
        for model, model_data in delay(list(deepcopy(data).items())):
            all_records_vals = []
            for xml_id, record_vals in model_data.items():
                # Extract the translations from the values
                for key in list(record_vals):
                    if '@' in key or key == '__translation_module__':
                        del record_vals[key]

                # Manage ids given as database id or xml_id
                if isinstance(xml_id, str) and (record := self.ref(xml_id, raise_if_not_found=False)):
                    xml_id = record.id

                if isinstance(xml_id, int):
                    record_vals['id'] = xml_id
                    xml_id = False
                else:
                    xml_id = self.company_xmlid(xml_id)

                all_records_vals.append({
                    'xml_id': xml_id,
                    'values': deref_values(record_vals, self.env[model]),
                    'noupdate': True,
                })
            created_records[model] = self.with_context(lang='en_US').env[model]._load_records(all_records_vals)
        return created_records