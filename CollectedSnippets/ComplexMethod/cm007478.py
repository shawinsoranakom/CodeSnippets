def _parse_video_data(self, video):
        title = video['name']

        entry_id, partner_id = [None] * 2
        for k in self._KALTURA_KEYS:
            k_url = video.get(k)
            if k_url:
                mobj = re.search(r'/p/(\d+)/.+?/entryId/([^/]+)/', k_url)
                if mobj:
                    partner_id, entry_id = mobj.groups()
                    break

        meta_categories = try_get(video, lambda x: x['meta']['categories'], list) or []
        categories = list(filter(None, [c.get('name') for c in meta_categories]))

        show_info = video.get('show_info') or {}

        return {
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (partner_id, entry_id),
            'ie_key': KalturaIE.ie_key(),
            'id': entry_id,
            'title': title,
            'description': self._get_object_description(video),
            'age_limit': parse_age_limit(video.get('mpaa_rating') or video.get('tv_rating')),
            'categories': categories,
            'series': show_info.get('show_name'),
            'season_number': int_or_none(show_info.get('season_num')),
            'season_id': show_info.get('season_id'),
            'episode_number': int_or_none(show_info.get('episode_num')),
        }