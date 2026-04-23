def _real_extract(self, url):
        locale, display_id, page_id = self._match_valid_url(url).group('locale', 'display_id', 'id')

        json_data = self._download_json(
            f'https://assets.msn.com/content/view/v2/Detail/{locale}/{page_id}', page_id)

        common_metadata = traverse_obj(json_data, {
            'title': ('title', {str}),
            'description': (('abstract', ('body', {clean_html})), {str}, filter, any),
            'timestamp': ('createdDateTime', {parse_iso8601}),
            'release_timestamp': ('publishedDateTime', {parse_iso8601}),
            'modified_timestamp': ('updatedDateTime', {parse_iso8601}),
            'thumbnail': ('thumbnail', 'image', 'url', {url_or_none}),
            'duration': ('videoMetadata', 'playTime', {int_or_none}),
            'tags': ('keywords', ..., {str}),
            'uploader': ('provider', 'name', {str}),
            'uploader_id': ('provider', 'id', {str}),
        })

        page_type = json_data['type']
        source_url = traverse_obj(json_data, ('sourceHref', {url_or_none}))
        if page_type == 'video':
            if traverse_obj(json_data, ('thirdPartyVideoPlayer', 'enabled')) and source_url:
                return self.url_result(source_url)
            formats = []
            subtitles = {}
            for file in traverse_obj(json_data, ('videoMetadata', 'externalVideoFiles', lambda _, v: url_or_none(v['url']))):
                file_url = file['url']
                ext = determine_ext(file_url)
                if ext == 'm3u8':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        file_url, page_id, 'mp4', m3u8_id='hls', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                elif ext == 'mpd':
                    fmts, subs = self._extract_mpd_formats_and_subtitles(
                        file_url, page_id, mpd_id='dash', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                else:
                    formats.append(
                        traverse_obj(file, {
                            'url': 'url',
                            'format_id': ('format', {str}),
                            'filesize': ('fileSize', {int_or_none}),
                            'height': ('height', {int_or_none}),
                            'width': ('width', {int_or_none}),
                        }))
            for caption in traverse_obj(json_data, ('videoMetadata', 'closedCaptions', lambda _, v: url_or_none(v['href']))):
                lang = caption.get('locale') or 'en-us'
                subtitles.setdefault(lang, []).append({
                    'url': caption['href'],
                    'ext': 'ttml',
                })

            return {
                'id': page_id,
                'display_id': display_id,
                'formats': formats,
                'subtitles': subtitles,
                **common_metadata,
            }
        elif page_type == 'webcontent':
            if not source_url:
                raise ExtractorError('Could not find source URL')
            return self.url_result(source_url)
        elif page_type == 'article':
            entries = []
            for embed_url in traverse_obj(json_data, ('socialEmbeds', ..., 'postUrl', {url_or_none})):
                entries.append(self.url_result(embed_url))

            return self.playlist_result(entries, page_id, **common_metadata)

        raise ExtractorError(f'Unsupported page type: {page_type}')