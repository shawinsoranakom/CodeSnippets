def download_url_ffmpeg(
    url, title, ext, params={}, total_size=0, output_dir='.', refer=None,
    merge=True, faker=False, stream=True
):
    assert url
    if dry_run:
        print_user_agent(faker=faker)
        print('Real URL:\n%s\n' % [url])
        if params.get('-y', False):  # None or unset ->False
            print('Real Playpath:\n%s\n' % [params.get('-y')])
        return

    if player:
        launch_player(player, [url])
        return

    from .processor.ffmpeg import has_ffmpeg_installed, ffmpeg_download_stream
    assert has_ffmpeg_installed(), 'FFmpeg not installed.'

    global output_filename
    if output_filename:
        dotPos = output_filename.rfind('.')
        if dotPos > 0:
            title = output_filename[:dotPos]
            ext = output_filename[dotPos+1:]
        else:
            title = output_filename

    title = tr(get_filename(title))

    ffmpeg_download_stream(url, title, ext, params, output_dir, stream=stream)