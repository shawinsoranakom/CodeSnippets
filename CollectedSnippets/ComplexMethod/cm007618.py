def _real_extract(self, url):
        guid = self._match_id(url)
        tp_path = 'PR1GhC/media/guid/2702976343/' + guid
        info = self._extract_theplatform_metadata(tp_path, guid)

        formats = []
        subtitles = {}
        first_e = None
        for asset_type in ('SD', 'HD'):
            # TODO: fixup ISM+none manifest URLs
            for f in ('MPEG4', 'MPEG-DASH+none', 'M3U+none'):
                try:
                    tp_formats, tp_subtitles = self._extract_theplatform_smil(
                        update_url_query('http://link.theplatform.%s/s/%s' % (self._TP_TLD, tp_path), {
                            'mbr': 'true',
                            'formats': f,
                            'assetTypes': asset_type,
                        }), guid, 'Downloading %s %s SMIL data' % (f.split('+')[0], asset_type))
                except ExtractorError as e:
                    if not first_e:
                        first_e = e
                    break
                for tp_f in tp_formats:
                    tp_f['quality'] = 1 if asset_type == 'HD' else 0
                formats.extend(tp_formats)
                subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        if first_e and not formats:
            raise first_e
        self._sort_formats(formats)

        fields = []
        for templ, repls in (('tvSeason%sNumber', ('', 'Episode')), ('mediasetprogram$%s', ('brandTitle', 'numberOfViews', 'publishInfo'))):
            fields.extend(templ % repl for repl in repls)
        feed_data = self._download_json(
            'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs/guid/-/' + guid,
            guid, fatal=False, query={'fields': ','.join(fields)})
        if feed_data:
            publish_info = feed_data.get('mediasetprogram$publishInfo') or {}
            info.update({
                'episode_number': int_or_none(feed_data.get('tvSeasonEpisodeNumber')),
                'season_number': int_or_none(feed_data.get('tvSeasonNumber')),
                'series': feed_data.get('mediasetprogram$brandTitle'),
                'uploader': publish_info.get('description'),
                'uploader_id': publish_info.get('channel'),
                'view_count': int_or_none(feed_data.get('mediasetprogram$numberOfViews')),
            })

        info.update({
            'id': guid,
            'formats': formats,
            'subtitles': subtitles,
        })
        return info