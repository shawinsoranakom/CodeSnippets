def _search_results(self, query, params=NO_DEFAULT, default_client='web'):
        data = {'query': query}
        if params is NO_DEFAULT:
            params = self._SEARCH_PARAMS
        if params:
            data['params'] = params

        content_keys = (
            ('contents', 'twoColumnSearchResultsRenderer', 'primaryContents', 'sectionListRenderer', 'contents'),
            ('onResponseReceivedCommands', 0, 'appendContinuationItemsAction', 'continuationItems'),
            # ytmusic search
            ('contents', 'tabbedSearchResultsRenderer', 'tabs', 0, 'tabRenderer', 'content', 'sectionListRenderer', 'contents'),
            ('continuationContents', ),
        )
        display_id = f'query "{query}"'
        check_get_keys = tuple({keys[0] for keys in content_keys})
        ytcfg = self._download_ytcfg(default_client, display_id) if not self.skip_webpage else {}
        self._report_playlist_authcheck(ytcfg, fatal=False)

        continuation_list = [None]
        search = None
        for page_num in itertools.count(1):
            data.update(continuation_list[0] or {})
            headers = self.generate_api_headers(
                ytcfg=ytcfg, visitor_data=self._extract_visitor_data(search), default_client=default_client)
            search = self._extract_response(
                item_id=f'{display_id} page {page_num}', ep='search', query=data,
                default_client=default_client, check_get_keys=check_get_keys, ytcfg=ytcfg, headers=headers)
            slr_contents = traverse_obj(search, *content_keys)
            yield from self._extract_entries({'contents': list(variadic(slr_contents))}, continuation_list)
            if not continuation_list[0]:
                break