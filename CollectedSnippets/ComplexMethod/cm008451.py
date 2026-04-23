def _extract_embed_urls(cls, url, webpage):
        # nelonen.fi
        settings = try_call(
            lambda: json.loads(re.search(
                r'jQuery\.extend\(Drupal\.settings, ({.+?})\);', webpage).group(1), strict=False))
        if settings:
            video_id = traverse_obj(settings, (
                'mediaCrossbowSettings', 'file', 'field_crossbow_video_id', 'und', 0, 'value'))
            if video_id:
                return [f'http://www.ruutu.fi/video/{video_id}']
        # hs.fi and is.fi
        settings = try_call(
            lambda: json.loads(re.search(
                '(?s)<script[^>]+id=[\'"]__NEXT_DATA__[\'"][^>]*>([^<]+)</script>',
                webpage).group(1), strict=False))
        if settings:
            video_ids = set(traverse_obj(settings, (
                'props', 'pageProps', 'page', 'assetData', 'splitBody', ..., 'video', 'sourceId')) or [])
            if video_ids:
                return [f'http://www.ruutu.fi/video/{v}' for v in video_ids]
            video_id = traverse_obj(settings, (
                'props', 'pageProps', 'page', 'assetData', 'mainVideo', 'sourceId'))
            if video_id:
                return [f'http://www.ruutu.fi/video/{video_id}']