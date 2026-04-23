def _parse_csv(self, template_code, model, module=None):
        Model = self.env[model]
        model_fields = Model._fields

        if module is None:
            module = self._get_chart_template_mapping().get(template_code)['module']
        assert re.fullmatch(r"[a-z0-9_]+", module)

        def evaluate(key, value, model_fields):
            if not value:
                return value
            if '@' in key:
                return value
            if '/' in key:
                return []
            if model_fields:
                if model_fields[key].type in ('boolean', 'int', 'float'):
                    return ast.literal_eval(value)
                if model_fields[key].type == 'char':
                    return value.strip()
            return value

        res = defaultdict(dict)
        for template in self._get_parent_template(template_code)[::-1] or ['']:
            try:
                with file_open(f"{module}/data/template/{model}{f'-{template}' if template else ''}.csv", 'r') as csv_file:
                    for row in csv.DictReader(csv_file):
                        if row['id']:
                            last_id = row['id']
                            res[row['id']].update({
                                key.split('/')[0]: evaluate(key, value, model_fields)
                                for key, value in row.items()
                                if key != 'id' and value and ('@' in key or key in model_fields)
                            })
                        create_added = set()
                        for key, value in row.items():
                            if '/' in key and value:
                                CurrentModel = Model
                                sub = res[last_id]
                                *model_path, fname = key.split('/')
                                path_str = "/".join(model_path)
                                for path_component in model_path:
                                    if path_str not in create_added:
                                        create_added.add(path_str)
                                        sub.setdefault(path_component, [])
                                        sub[path_component].append(Command.create({}))
                                    sub = sub[path_component][-1][2]
                                    CurrentModel = self.env[CurrentModel[path_component]._name]
                                sub[fname] = evaluate(fname, value, CurrentModel._fields)

            except FileNotFoundError:
                _logger.debug("No file %s found for template '%s'", model, module)
        return res