def _real_extract(self, url):
        guid = self._match_id(url)
        tp_path = f'PR1GhC/media/guid/2702976343/{guid}'
        info = self._extract_theplatform_metadata(tp_path, guid)

        formats = []
        subtitles = {}
        first_e = geo_e = None
        asset_type = 'geoNo:HD,browser,geoIT|geoNo:HD,geoIT|geoNo:SD,browser,geoIT|geoNo:SD,geoIT|geoNo|HD|SD'
        # TODO: fixup ISM+none manifest URLs
        for f in ('MPEG4', 'MPEG-DASH', 'M3U'):
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    update_url_query(f'http://link.theplatform.{self._TP_TLD}/s/{tp_path}', {
                        'mbr': 'true',
                        'formats': f,
                        'assetTypes': asset_type,
                    }), guid, f'Downloading {f.split("+")[0]} SMIL data')
            except ExtractorError as e:
                if e.orig_msg == 'None of the available releases match the specified AssetType, ProtectionScheme, and/or Format preferences':
                    e.orig_msg = 'This video is DRM protected'
                if not geo_e and isinstance(e, GeoRestrictedError):
                    geo_e = e
                if not first_e:
                    first_e = e
                continue
            self._check_drm_formats(tp_formats, guid)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)

        # check for errors and report them
        if (first_e or geo_e) and not formats:
            raise geo_e or first_e

        feed_data = self._download_json(
            f'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs-v2/guid/-/{guid}',
            guid, fatal=False)
        if feed_data:
            publish_info = feed_data.get('mediasetprogram$publishInfo') or {}
            thumbnails = feed_data.get('thumbnails') or {}
            thumbnail = None
            for key, value in thumbnails.items():
                if key.startswith('image_keyframe_poster-'):
                    thumbnail = value.get('url')
                    break

            info.update({
                'description': info.get('description') or feed_data.get('description') or feed_data.get('longDescription'),
                'uploader': publish_info.get('description'),
                'uploader_id': publish_info.get('channel'),
                'view_count': int_or_none(feed_data.get('mediasetprogram$numberOfViews')),
                'thumbnail': thumbnail,
            })

            if feed_data.get('programType') == 'episode':
                info.update({
                    'episode_number': int_or_none(
                        feed_data.get('tvSeasonEpisodeNumber')),
                    'season_number': int_or_none(
                        feed_data.get('tvSeasonNumber')),
                    'series': feed_data.get('mediasetprogram$brandTitle'),
                })

        info.update({
            'id': guid,
            'formats': formats,
            'subtitles': subtitles,
        })
        return info