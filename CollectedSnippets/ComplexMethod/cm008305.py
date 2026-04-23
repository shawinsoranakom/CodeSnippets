def _extract_feed_info(self, provider_id, feed_id, filter_query, video_id, custom_fields=None, asset_types_query={}, account_id=None):
        real_url = self._URL_TEMPLATE % (self.http_scheme(), provider_id, feed_id, filter_query)
        entry = self._download_json(real_url, video_id)['entries'][0]
        main_smil_url = 'http://link.theplatform.com/s/%s/media/guid/%d/%s' % (provider_id, account_id, entry['guid']) if account_id else entry.get('plmedia$publicUrl')

        formats = []
        subtitles = {}
        first_video_id = None
        duration = None
        asset_types = []
        for item in entry['media$content']:
            smil_url = item['plfile$url']
            cur_video_id = ThePlatformIE._match_id(smil_url)
            if first_video_id is None:
                first_video_id = cur_video_id
                duration = float_or_none(item.get('plfile$duration'))
            file_asset_types = item.get('plfile$assetTypes') or parse_qs(smil_url)['assetTypes']
            for asset_type in file_asset_types:
                if asset_type in asset_types:
                    continue
                asset_types.append(asset_type)
                query = {
                    'mbr': 'true',
                    'formats': item['plfile$format'],
                    'assetTypes': asset_type,
                }
                if asset_type in asset_types_query:
                    query.update(asset_types_query[asset_type])
                cur_formats, cur_subtitles = self._extract_theplatform_smil(update_url_query(
                    main_smil_url or smil_url, query), video_id, f'Downloading SMIL data for {asset_type}')
                formats.extend(cur_formats)
                subtitles = self._merge_subtitles(subtitles, cur_subtitles)

        thumbnails = [{
            'url': thumbnail['plfile$url'],
            'width': int_or_none(thumbnail.get('plfile$width')),
            'height': int_or_none(thumbnail.get('plfile$height')),
        } for thumbnail in entry.get('media$thumbnails', [])]

        timestamp = int_or_none(entry.get('media$availableDate'), scale=1000)
        categories = [item['media$name'] for item in entry.get('media$categories', [])]

        ret = self._extract_theplatform_metadata(f'{provider_id}/{first_video_id}', video_id)
        subtitles = self._merge_subtitles(subtitles, ret['subtitles'])
        ret.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'duration': duration,
            'timestamp': timestamp,
            'categories': categories,
        })
        if custom_fields:
            ret.update(custom_fields(entry))

        return ret