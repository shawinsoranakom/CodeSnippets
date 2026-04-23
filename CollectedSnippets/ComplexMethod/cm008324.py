def _entries(self, channel_name, *args):
        """
        Subclasses must define _make_variables() and _extract_entry(),
        as well as set _OPERATION_NAME, _ENTRY_KIND, _EDGE_KIND, and _NODE_KIND
        """
        cursor = None
        variables_common = self._make_variables(channel_name, *args)
        entries_key = f'{self._ENTRY_KIND}s'
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
                f'Downloading {self._NODE_KIND}s GraphQL page {page_num}',
                fatal=False)
            # Avoid extracting random/unrelated entries when channel_name doesn't exist
            # See https://github.com/yt-dlp/yt-dlp/issues/15450
            if traverse_obj(page, (0, 'data', 'user', 'id', {str})) == '':
                raise ExtractorError(f'Channel "{channel_name}" not found', expected=True)
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
            if not cursor or not isinstance(cursor, str):
                break