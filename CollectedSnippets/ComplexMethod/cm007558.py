def _entries(self, channel_name, *args):
        cursor = None
        variables_common = self._make_variables(channel_name, *args)
        entries_key = '%ss' % self._ENTRY_KIND
        for page_num in itertools.count(1):
            variables = variables_common.copy()
            variables['limit'] = self._PAGE_LIMIT
            if cursor:
                variables['cursor'] = cursor
            page = self._download_gql(
                channel_name, [{
                    'operationName': self._OPERATION_NAME,
                    'variables': variables,
                }],
                'Downloading %ss GraphQL page %s' % (self._NODE_KIND, page_num),
                fatal=False)
            if not page:
                break
            edges = try_get(
                page, lambda x: x[0]['data']['user'][entries_key]['edges'], list)
            if not edges:
                break
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                if edge.get('__typename') != self._EDGE_KIND:
                    continue
                node = edge.get('node')
                if not isinstance(node, dict):
                    continue
                if node.get('__typename') != self._NODE_KIND:
                    continue
                entry = self._extract_entry(node)
                if entry:
                    cursor = edge.get('cursor')
                    yield entry
            if not cursor or not isinstance(cursor, compat_str):
                break