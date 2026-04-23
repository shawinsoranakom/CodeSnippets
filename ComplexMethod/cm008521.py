def _get_subtitles(self, video_id, variants, ios_playlist_url, headers, *args, **kwargs):
        subtitles = {}
        # Prefer last matching featureset
        # See: https://github.com/yt-dlp/yt-dlp/issues/986
        platform_tag_subs, featureset_subs = next(
            ((platform_tag, featureset)
             for platform_tag, featuresets in reversed(list(variants.items())) for featureset in featuresets
             if try_get(featureset, lambda x: x[2]) == 'outband-webvtt'),
            (None, None))

        if platform_tag_subs and featureset_subs:
            subs_playlist = self._call_api(
                video_id, ios_playlist_url, headers, platform_tag_subs, featureset_subs, fatal=False)
            subs = try_get(subs_playlist, lambda x: x['Playlist']['Video']['Subtitles'], list) or []
            for sub in subs:
                if not isinstance(sub, dict):
                    continue
                href = url_or_none(sub.get('Href'))
                if not href:
                    continue
                subtitles.setdefault('en', []).append({'url': href})
        return subtitles