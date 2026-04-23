def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data = self._download_json(
            'https://cfunity.nfhsnetwork.com/v2/game_or_event/' + video_id,
            video_id)
        publisher = data.get('publishers')[0]  # always exists
        broadcast = (publisher.get('broadcasts') or publisher.get('vods'))[0]  # some (older) videos don't have a broadcasts object
        uploader = publisher.get('formatted_name') or publisher.get('name')
        uploader_id = publisher.get('publisher_key')
        pub_type = publisher.get('type')
        uploader_prefix = (
            'schools' if pub_type == 'school'
            else 'associations' if 'association' in pub_type
            else 'affiliates' if (pub_type == 'publisher' or pub_type == 'affiliate')
            else 'schools')
        uploader_page = 'https://www.nfhsnetwork.com/{}/{}'.format(uploader_prefix, publisher.get('slug'))
        location = '{}, {}'.format(data.get('city'), data.get('state_name'))
        description = broadcast.get('description')
        is_live = broadcast.get('on_air') or broadcast.get('status') == 'on_air' or False

        timestamp = unified_timestamp(data.get('local_start_time'))
        upload_date = unified_strdate(data.get('local_start_time'))

        title = (
            self._og_search_title(webpage)
            or self._html_search_regex(r'<h1 class="sr-hidden">(.*?)</h1>', webpage, 'title'))
        title = title.split('|')[0].strip()

        video_type = 'broadcasts' if is_live else 'vods'
        key = broadcast.get('key') if is_live else try_get(publisher, lambda x: x['vods'][0]['key'])
        m3u8_url = self._download_json(
            f'https://cfunity.nfhsnetwork.com/v2/{video_type}/{key}/url',
            video_id).get('video_url')

        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', live=is_live)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': uploader_page,
            'location': location,
            'upload_date': upload_date,
            'is_live': is_live,
            '_format_sort_fields': ('res', 'tbr'),
        }