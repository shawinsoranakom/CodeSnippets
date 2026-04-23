def selector_function(ctx):
                    formats = list(ctx['formats'])
                    if not formats:
                        return
                    if format_spec == 'all':
                        for f in formats:
                            yield f
                    elif format_spec in ['best', 'worst', None]:
                        format_idx = 0 if format_spec == 'worst' else -1
                        audiovideo_formats = [
                            f for f in formats
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        if audiovideo_formats:
                            yield audiovideo_formats[format_idx]
                        # for extractors with incomplete formats (audio only (soundcloud)
                        # or video only (imgur)) we will fallback to best/worst
                        # {video,audio}-only format
                        elif ctx['incomplete_formats']:
                            yield formats[format_idx]
                    elif format_spec == 'bestaudio':
                        audio_formats = [
                            f for f in formats
                            if f.get('vcodec') == 'none']
                        if audio_formats:
                            yield audio_formats[-1]
                    elif format_spec == 'worstaudio':
                        audio_formats = [
                            f for f in formats
                            if f.get('vcodec') == 'none']
                        if audio_formats:
                            yield audio_formats[0]
                    elif format_spec == 'bestvideo':
                        video_formats = [
                            f for f in formats
                            if f.get('acodec') == 'none']
                        if video_formats:
                            yield video_formats[-1]
                    elif format_spec == 'worstvideo':
                        video_formats = [
                            f for f in formats
                            if f.get('acodec') == 'none']
                        if video_formats:
                            yield video_formats[0]
                    else:
                        extensions = ['mp4', 'flv', 'webm', '3gp', 'm4a', 'mp3', 'ogg', 'aac', 'wav']
                        if format_spec in extensions:
                            filter_f = lambda f: f['ext'] == format_spec
                        else:
                            filter_f = lambda f: f['format_id'] == format_spec
                        matches = list(filter(filter_f, formats))
                        if matches:
                            yield matches[-1]