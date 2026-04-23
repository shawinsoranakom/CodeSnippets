def set_compat_opts(opts):
    def _unused_compat_opt(name):
        if name not in opts.compat_opts:
            return False
        opts.compat_opts.discard(name)
        opts.compat_opts.update([f'*{name}'])
        return True

    def set_default_compat(compat_name, opt_name, default=True, remove_compat=True):
        attr = getattr(opts, opt_name)
        if compat_name in opts.compat_opts:
            if attr is None:
                setattr(opts, opt_name, not default)
                return True
            else:
                if remove_compat:
                    _unused_compat_opt(compat_name)
                return False
        elif attr is None:
            setattr(opts, opt_name, default)
        return None

    set_default_compat('abort-on-error', 'ignoreerrors', 'only_download')
    set_default_compat('no-playlist-metafiles', 'allow_playlist_files')
    set_default_compat('no-clean-infojson', 'clean_infojson')
    if 'no-attach-info-json' in opts.compat_opts:
        if opts.embed_infojson:
            _unused_compat_opt('no-attach-info-json')
        else:
            opts.embed_infojson = False
    if 'format-sort' in opts.compat_opts:
        opts.format_sort.extend(FormatSorter.ytdl_default)
    elif 'prefer-vp9-sort' in opts.compat_opts:
        FormatSorter.default = FormatSorter._prefer_vp9_sort

    if 'mtime-by-default' in opts.compat_opts:
        if opts.updatetime is None:
            opts.updatetime = True
        else:
            _unused_compat_opt('mtime-by-default')

    _video_multistreams_set = set_default_compat('multistreams', 'allow_multiple_video_streams', False, remove_compat=False)
    _audio_multistreams_set = set_default_compat('multistreams', 'allow_multiple_audio_streams', False, remove_compat=False)
    if _video_multistreams_set is False and _audio_multistreams_set is False:
        _unused_compat_opt('multistreams')
    if 'filename' in opts.compat_opts:
        if opts.outtmpl.get('default') is None:
            opts.outtmpl.update({'default': '%(title)s-%(id)s.%(ext)s'})
        else:
            _unused_compat_opt('filename')