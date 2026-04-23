def _search_results(self, query, params):
        data = {
            'context': {
                'client': {
                    'clientName': 'WEB',
                    'clientVersion': '2.20201021.03.00',
                },
            },
            'query': query,
        }
        if params:
            data['params'] = params
        for page_num in itertools.count(1):
            search = self._download_json(
                'https://www.youtube.com/youtubei/v1/search',
                video_id='query "%s"' % query,
                note='Downloading page %s' % page_num,
                errnote='Unable to download API page', fatal=False,
                data=json.dumps(data).encode('utf8'),
                query={
                    # 'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
                    'prettyPrint': 'false',
                },
                headers={'content-type': 'application/json'})
            if not search:
                break
            slr_contents = traverse_obj(
                search,
                ('contents', 'twoColumnSearchResultsRenderer', 'primaryContents',
                 'sectionListRenderer', 'contents'),
                ('onResponseReceivedCommands', 0, 'appendContinuationItemsAction',
                 'continuationItems'),
                expected_type=list)
            if not slr_contents:
                break
            for video in traverse_obj(
                    slr_contents,
                    (Ellipsis, 'itemSectionRenderer', 'contents',
                     Ellipsis, 'videoRenderer',
                     T(lambda v: v if v.get('videoId') else None))):
                yield self._extract_video(video)

            token = traverse_obj(
                slr_contents,
                (-1, 'continuationItemRenderer', 'continuationEndpoint',
                 'continuationCommand', 'token', T(compat_str)))
            if not token:
                break
            data['continuation'] = token