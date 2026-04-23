def _extract_graphql(self, data, url):
        # Parses GraphQL queries containing videos and generates a playlist.
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        uploader_id = self._match_id(url)
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        cursor = ''
        for page_num in itertools.count(1):
            variables = {
                'first': 12,
                'after': cursor,
            }
            variables.update(self._query_vars_for(data))
            variables = json.dumps(variables)

            if self._gis_tmpl:
                gis_tmpls = [self._gis_tmpl]
            else:
                gis_tmpls = [
                    '%s' % rhx_gis,
                    '',
                    '%s:%s' % (rhx_gis, csrf_token),
                    '%s:%s:%s' % (rhx_gis, csrf_token, std_headers['User-Agent']),
                ]

            # try all of the ways to generate a GIS query, and not only use the
            # first one that works, but cache it for future requests
            for gis_tmpl in gis_tmpls:
                try:
                    json_data = self._download_json(
                        'https://www.instagram.com/graphql/query/', uploader_id,
                        'Downloading JSON page %d' % page_num, headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-Instagram-GIS': hashlib.md5(
                                ('%s:%s' % (gis_tmpl, variables)).encode('utf-8')).hexdigest(),
                        }, query={
                            'query_hash': self._QUERY_HASH,
                            'variables': variables,
                        })
                    media = self._parse_timeline_from(json_data)
                    self._gis_tmpl = gis_tmpl
                    break
                except ExtractorError as e:
                    # if it's an error caused by a bad query, and there are
                    # more GIS templates to try, ignore it and keep trying
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if gis_tmpl != gis_tmpls[-1]:
                            continue
                    raise

            edges = media.get('edges')
            if not edges or not isinstance(edges, list):
                break

            for edge in edges:
                node = edge.get('node')
                if not node or not isinstance(node, dict):
                    continue
                if node.get('__typename') != 'GraphVideo' and node.get('is_video') is not True:
                    continue
                video_id = node.get('shortcode')
                if not video_id:
                    continue

                info = self.url_result(
                    'https://instagram.com/p/%s/' % video_id,
                    ie=InstagramIE.ie_key(), video_id=video_id)

                description = try_get(
                    node, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                    compat_str)
                thumbnail = node.get('thumbnail_src') or node.get('display_src')
                timestamp = int_or_none(node.get('taken_at_timestamp'))

                comment_count = get_count('to_comment')
                like_count = get_count('preview_like')
                view_count = int_or_none(node.get('video_view_count'))

                info.update({
                    'description': description,
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'comment_count': comment_count,
                    'like_count': like_count,
                    'view_count': view_count,
                })

                yield info

            page_info = media.get('page_info')
            if not page_info or not isinstance(page_info, dict):
                break

            has_next_page = page_info.get('has_next_page')
            if not has_next_page:
                break

            cursor = page_info.get('end_cursor')
            if not cursor or not isinstance(cursor, compat_str):
                break