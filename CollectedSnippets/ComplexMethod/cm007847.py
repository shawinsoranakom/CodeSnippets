def _entries(self, tab, item_id, webpage):
        tab_content = try_get(tab, lambda x: x['content'], dict)
        if not tab_content:
            return
        slr_renderer = try_get(tab_content, lambda x: x['sectionListRenderer'], dict)
        if slr_renderer:
            is_channels_tab = tab.get('title') == 'Channels'
            continuation = None
            for is_renderer in traverse_obj(slr_renderer, (
                    'contents', Ellipsis, 'itemSectionRenderer', T(dict))):
                for isr_content in traverse_obj(is_renderer, (
                        'contents', Ellipsis, T(dict))):
                    renderer = isr_content.get('playlistVideoListRenderer')
                    if renderer:
                        for entry in self._playlist_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('gridRenderer')
                    if renderer:
                        for entry in self._grid_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('shelfRenderer')
                    if renderer:
                        for entry in self._shelf_entries(renderer, not is_channels_tab):
                            yield entry
                        continue
                    renderer = isr_content.get('backstagePostThreadRenderer')
                    if renderer:
                        for entry in self._post_thread_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('videoRenderer')
                    if renderer:
                        entry = self._video_entry(renderer)
                        if entry:
                            yield entry
                    renderer = isr_content.get('richGridRenderer')
                    if renderer:
                        for from_ in self._rich_grid_entries(
                                traverse_obj(renderer, ('contents', Ellipsis, T(dict)))):
                            yield from_
                        continuation = self._extract_continuation(renderer)
                        continue

                if not continuation:
                    continuation = self._extract_continuation(is_renderer)
            if not continuation:
                continuation = self._extract_continuation(slr_renderer)
        else:
            rich_grid_renderer = tab_content.get('richGridRenderer')
            if not rich_grid_renderer:
                return
            for from_ in self._rich_grid_entries(
                    traverse_obj(rich_grid_renderer, ('contents', Ellipsis, T(dict)))):
                yield from_

            continuation = self._extract_continuation(rich_grid_renderer)

        ytcfg = self._extract_ytcfg(item_id, webpage)
        client_version = try_get(
            ytcfg, lambda x: x['INNERTUBE_CLIENT_VERSION'], compat_str) or '2.20210407.08.00'

        headers = {
            'x-youtube-client-name': '1',
            'x-youtube-client-version': client_version,
            'content-type': 'application/json',
        }

        context = try_get(ytcfg, lambda x: x['INNERTUBE_CONTEXT'], dict) or {
            'client': {
                'clientName': 'WEB',
                'clientVersion': client_version,
            },
        }
        visitor_data = try_get(context, lambda x: x['client']['visitorData'], compat_str)

        identity_token = self._extract_identity_token(ytcfg, webpage)
        if identity_token:
            headers['x-youtube-identity-token'] = identity_token

        data = {
            'context': context,
        }

        for page_num in itertools.count(1):
            if not continuation:
                break
            if visitor_data:
                headers['X-Goog-Visitor-Id'] = visitor_data
            data['continuation'] = continuation['continuation']
            data['clickTracking'] = {
                'clickTrackingParams': continuation['itct'],
            }
            count = 0
            retries = 3
            while count <= retries:
                try:
                    # Downloading page may result in intermittent 5xx HTTP error
                    # that is usually worked around with a retry
                    response = self._download_json(
                        'https://www.youtube.com/youtubei/v1/browse',
                        None, 'Downloading page %d%s' % (page_num, ' (retry #%d)' % count if count else ''),
                        query={
                            # 'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
                            'prettyPrint': 'false',
                        },
                        headers=headers, data=json.dumps(data).encode('utf8'))
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code in (500, 503):
                        count += 1
                        if count <= retries:
                            continue
                    raise
            if not response:
                break

            visitor_data = try_get(
                response, lambda x: x['responseContext']['visitorData'], compat_str) or visitor_data

            continuation_contents = try_get(
                response, lambda x: x['continuationContents'], dict)
            if continuation_contents:
                continuation_renderer = continuation_contents.get('playlistVideoListContinuation')
                if continuation_renderer:
                    for entry in self._playlist_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                continuation_renderer = continuation_contents.get('gridContinuation')
                if continuation_renderer:
                    for entry in self._grid_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                continuation_renderer = continuation_contents.get('itemSectionContinuation')
                if continuation_renderer:
                    for entry in self._post_thread_continuation_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue

            on_response_received = dict_get(response, ('onResponseReceivedActions', 'onResponseReceivedEndpoints'))
            continuation_items = try_get(
                on_response_received, lambda x: x[0]['appendContinuationItemsAction']['continuationItems'], list)
            if continuation_items:
                continuation_item = continuation_items[0]
                if not isinstance(continuation_item, dict):
                    continue
                renderer = self._extract_grid_item_renderer(continuation_item)
                if renderer:
                    grid_renderer = {'items': continuation_items}
                    for entry in self._grid_entries(grid_renderer):
                        yield entry
                    continuation = self._extract_continuation(grid_renderer)
                    continue
                renderer = continuation_item.get('playlistVideoRenderer') or continuation_item.get('itemSectionRenderer')
                if renderer:
                    video_list_renderer = {'contents': continuation_items}
                    for entry in self._playlist_entries(video_list_renderer):
                        yield entry
                    continuation = self._extract_continuation(video_list_renderer)
                    continue
                renderer = continuation_item.get('backstagePostThreadRenderer')
                if renderer:
                    continuation_renderer = {'contents': continuation_items}
                    for entry in self._post_thread_continuation_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                renderer = continuation_item.get('richItemRenderer')
                if renderer:
                    for entry in self._rich_grid_entries(continuation_items):
                        yield entry
                    continuation = self._extract_continuation({'contents': continuation_items})
                    continue

            break