def get_video_url_data(video_url, autoplay=False, loop=False,
                       hide_controls=False, hide_fullscreen=False,
                       hide_dm_logo=False, hide_dm_share=False,
                       start_from=False):
    """ Computes the platform name, the embed_url, the video id and the video params of the given URL
        (or error message in case of invalid URL).
    """
    source = get_video_source_data(video_url)
    if source is None:
        return {'error': True, 'message': _('The provided url is invalid')}

    embed_url = video_url
    platform, video_id, platform_match = source

    params = {}
    if start_from == "00:00":
        start_from = "0"
    if platform == 'youtube':
        params['rel'] = 0
        params['autoplay'] = autoplay and 1 or 0
        if start_from:
            params["start"] = start_from.rstrip("s")
        if autoplay:
            params['mute'] = 1
            # The youtube js api is needed for autoplay on mobile. Note: this
            # was added as a fix, old customers may have autoplay videos
            # without this, which will make their video autoplay on desktop but
            # not in mobile (so no behavior change was done in stable, this
            # should not be migrated).
            params['enablejsapi'] = 1
        if hide_controls:
            params['controls'] = 0
        if loop:
            params['loop'] = 1
            params['playlist'] = video_id
        if hide_fullscreen:
            params['fs'] = 0
        yt_extra = platform_match[1] or ''
        embed_url = f"//www.youtube{yt_extra}.com/embed/{video_id}?{url_encode(params)}"
    elif platform == 'vimeo':
        params['autoplay'] = autoplay and 1 or 0
        # Always enable "do not track" parameter.
        params['dnt'] = 1
        if autoplay:
            params['muted'] = 1
            params['autopause'] = 0
        if hide_controls:
            params['controls'] = 0
        if loop:
            params['loop'] = 1
        groups = platform_match.groupdict()
        if groups.get('hash'):
            params['h'] = groups['hash']
        elif groups.get('params'):
            url_params = parse_qs(groups['params'])
            if 'h' in url_params:
                params['h'] = url_params['h'][0]
        embed_url = f"//player.vimeo.com/video/{video_id}?{url_encode(params)}"
        if start_from:
            embed_url = f"{embed_url}#t={start_from}"
    elif platform == 'dailymotion':
        if start_from:
            params["startTime"] = start_from.rstrip("s")
        embed_url = f"//geo.dailymotion.com/player.html?video={video_id}&{url_encode(params)}"
    elif platform == 'instagram':
        embed_url = f'//www.instagram.com/p/{video_id}/embed/'
    elif platform == "facebook":
        embed_url = f"//facebook.com/plugins/video.php?href=https://www.facebook.com/username/videos/{video_id}/"

    return {
        'platform': platform,
        'embed_url': embed_url,
        'video_id': video_id,
        'params': params
    }