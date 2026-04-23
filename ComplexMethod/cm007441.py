def _extract_video_info(self, content_id, site='cbs', mpx_acc=2198311517):
        items_data = self._download_xml(
            'http://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': site, 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title', True)
        tp_path = 'dJ5BDC/media/guid/%d/%s' % (mpx_acc, content_id)
        tp_release_url = 'http://link.theplatform.com/s/' + tp_path

        asset_types = []
        subtitles = {}
        formats = []
        last_e = None
        for item in items_data.findall('.//item'):
            asset_type = xpath_text(item, 'assetType')
            if not asset_type or asset_type in asset_types or 'HLS_FPS' in asset_type or 'DASH_CENC' in asset_type:
                continue
            asset_types.append(asset_type)
            query = {
                'mbr': 'true',
                'assetTypes': asset_type,
            }
            if asset_type.startswith('HLS') or asset_type in ('OnceURL', 'StreamPack'):
                query['formats'] = 'MPEG4,M3U'
            elif asset_type in ('RTMP', 'WIFI', '3G'):
                query['formats'] = 'MPEG4,FLV'
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    update_url_query(tp_release_url, query), content_id,
                    'Downloading %s SMIL data' % asset_type)
            except ExtractorError as e:
                last_e = e
                continue
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        if last_e and not formats:
            raise last_e
        self._sort_formats(formats)

        info = self._extract_theplatform_metadata(tp_path, content_id)
        info.update({
            'id': content_id,
            'title': title,
            'series': xpath_text(video_data, 'seriesTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'duration': int_or_none(xpath_text(video_data, 'videoLength'), 1000),
            'thumbnail': xpath_text(video_data, 'previewImageURL'),
            'formats': formats,
            'subtitles': subtitles,
        })
        return info