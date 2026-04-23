def _fill_sorting_fields(format):
        # Determine missing protocol
        if not format.get('protocol'):
            format['protocol'] = determine_protocol(format)

        # Determine missing ext
        if not format.get('ext') and 'url' in format:
            format['ext'] = determine_ext(format['url']).lower()
        if format.get('vcodec') == 'none':
            format['audio_ext'] = format['ext'] if format.get('acodec') != 'none' else 'none'
            format['video_ext'] = 'none'
        else:
            format['video_ext'] = format['ext']
            format['audio_ext'] = 'none'
        # if format.get('preference') is None and format.get('ext') in ('f4f', 'f4m'):  # Not supported?
        #    format['preference'] = -1000

        if format.get('preference') is None and format.get('ext') == 'flv' and re.match('[hx]265|he?vc?', format.get('vcodec') or ''):
            # HEVC-over-FLV is out-of-spec by FLV's original spec
            # ref. https://trac.ffmpeg.org/ticket/6389
            # ref. https://github.com/yt-dlp/yt-dlp/pull/5821
            format['preference'] = -100

        # Determine missing bitrates
        if format.get('vcodec') == 'none':
            format['vbr'] = 0
        if format.get('acodec') == 'none':
            format['abr'] = 0
        if not format.get('vbr') and format.get('vcodec') != 'none':
            format['vbr'] = try_call(lambda: format['tbr'] - format['abr']) or None
        if not format.get('abr') and format.get('acodec') != 'none':
            format['abr'] = try_call(lambda: format['tbr'] - format['vbr']) or None
        if not format.get('tbr'):
            format['tbr'] = try_call(lambda: format['vbr'] + format['abr']) or None