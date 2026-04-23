def _extract_video_info(self, content_id, site='cbs', mpx_acc=2198311517):
        items_data = self._download_xml(
            'https://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': site, 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title') or xpath_text(video_data, 'videotitle', 'title')

        asset_types = {}
        has_drm = False
        for item in items_data.findall('.//item'):
            asset_type = xpath_text(item, 'assetType')
            query = {
                'mbr': 'true',
                'assetTypes': asset_type,
            }
            if not asset_type:
                # fallback for content_ids that videoPlayerService doesn't return anything for
                asset_type = 'fallback'
                query['formats'] = 'M3U+none,MPEG4,M3U+appleHlsEncryption,MP3'
                del query['assetTypes']
            if asset_type in asset_types:
                continue
            elif any(excluded in asset_type for excluded in ('HLS_FPS', 'DASH_CENC', 'OnceURL')):
                if 'DASH_CENC' in asset_type:
                    has_drm = True
                continue
            if asset_type.startswith('HLS') or 'StreamPack' in asset_type:
                query['formats'] = 'MPEG4,M3U'
            elif asset_type in ('RTMP', 'WIFI', '3G'):
                query['formats'] = 'MPEG4,FLV'
            asset_types[asset_type] = query

        if not asset_types and has_drm:
            self.report_drm(content_id)

        return self._extract_common_video_info(content_id, asset_types, mpx_acc, extra_info={
            'title': title,
            'series': xpath_text(video_data, 'seriesTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'duration': int_or_none(xpath_text(video_data, 'videoLength'), 1000),
            'thumbnail': url_or_none(xpath_text(video_data, 'previewImageURL')),
        })