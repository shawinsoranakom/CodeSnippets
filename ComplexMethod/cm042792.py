def get_output_filename(urls, title, ext, output_dir, merge, **kwargs):
    # lame hack for the --output-filename option
    global output_filename
    if output_filename:
        result = output_filename
        if kwargs.get('part', -1) >= 0:
            result = '%s[%02d]' % (result, kwargs.get('part'))
        if ext:
            result = '%s.%s' % (result, ext)
        return result

    merged_ext = ext
    if (len(urls) > 1) and merge:
        from .processor.ffmpeg import has_ffmpeg_installed
        if ext in ['flv', 'f4v']:
            if has_ffmpeg_installed():
                merged_ext = 'mp4'
            else:
                merged_ext = 'flv'
        elif ext == 'mp4':
            merged_ext = 'mp4'
        elif ext == 'ts':
            if has_ffmpeg_installed():
                merged_ext = 'mkv'
            else:
                merged_ext = 'ts'
    result = title
    if kwargs.get('part', -1) >= 0:
        result = '%s[%02d]' % (result, kwargs.get('part'))
    result = '%s.%s' % (result, merged_ext)
    return result.replace("'", "_")