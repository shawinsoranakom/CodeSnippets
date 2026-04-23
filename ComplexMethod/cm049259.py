def base(self, data):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain', 'import_compat')(params)

        Model = request.env[model].with_context(import_compat=import_compat, **params.get('context', {}))
        if not Model._is_an_ordinary_table():
            fields = [field for field in fields if field['name'] != 'id']

        field_names = [f['name'] for f in fields]
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]

        records = Model.browse(ids) if ids else Model.search(domain)

        groupby = params.get('groupby')
        if not import_compat and groupby:
            export_data = records.export_data(['.id'] + field_names).get('datas', [])
            groupby_type = [Model._fields[x.split(':', 1)[0].split('.', 1)[0]].type for x in groupby]
            tree = GroupsTreeNode(Model, field_names, groupby, groupby_type)
            if ids:
                domain = [('id', 'in', ids)]
                SearchModel = Model.with_context(active_test=False)
            else:
                SearchModel = Model
            groups_data = SearchModel.formatted_read_group(domain, groupby, ['__count', 'id:array_agg'])

            # Build a map from record ID to its export rows
            record_rows = {}
            current_id = None
            for row in export_data:
                if row[0]:  # First column is the record ID
                    current_id = int(row[0])
                    record_rows[current_id] = []
                record_rows[current_id].append(row[1:])

            # To preserve the natural model order, base the data order on the result of `export_data`,
            # which comes from a `Model.search`

            # 1. Map each record ID to its group index
            groups = [group['id:array_agg'] for group in groups_data]
            record_to_group = defaultdict(list)
            for group_index, ids in enumerate(groups):
                for record_id in ids:
                    record_to_group[record_id].append(group_index)

            # 2. Iterate on the result of `export_data` and assign each data to its right group
            grouped_rows = [[] for _ in groups]
            for record_id, rows in record_rows.items():
                for group_index in record_to_group[record_id]:
                    grouped_rows[group_index].extend(rows)

            # 3. Insert one leaf per group, providing the group information and its data
            for group_info, group_rows in zip(groups_data, grouped_rows):
                tree.insert_leaf(group_info, group_rows)

            response_data = self.from_group_data(fields, columns_headers, tree)
        else:
            export_data = records.export_data(field_names).get('datas', [])
            response_data = self.from_data(fields, columns_headers, export_data)

        _logger.info(
            "User %d exported %d %r records from %s. Fields: %s. %s: %s",
            request.env.user.id, len(records.ids), records._name, request.httprequest.environ['REMOTE_ADDR'],
            ','.join(field_names),
            'IDs sample' if ids else 'Domain',
            records.ids[:10] if ids else domain,
        )

        # TODO: call `clean_filename` directly in `content_disposition`?
        return request.make_response(response_data,
            headers=[('Content-Disposition',
                            content_disposition(
                                osutil.clean_filename(self.filename(model) + self.extension))),
                     ('Content-Type', self.content_type)],
        )