def download_urls(
    urls, title, ext, total_size, output_dir='.', refer=None, merge=True,
    faker=False, headers={}, **kwargs
):
    assert urls
    if json_output:
        json_output_.download_urls(
            urls=urls, title=title, ext=ext, total_size=total_size,
            refer=refer
        )
        return
    if dry_run:
        print_user_agent(faker=faker)
        try:
            print('Real URLs:\n%s' % '\n'.join(urls))
        except:
            print('Real URLs:\n%s' % '\n'.join([j for i in urls for j in i]))
        return

    if player:
        launch_player(player, urls)
        return

    if not total_size:
        try:
            total_size = urls_size(urls, faker=faker, headers=headers)
        except:
            import traceback
            traceback.print_exc(file=sys.stdout)
            pass

    title = tr(get_filename(title))
    if postfix and 'vid' in kwargs:
        title = "%s [%s]" % (title, kwargs['vid'])
    if prefix is not None:
        title = "[%s] %s" % (prefix, title)
    output_filename = get_output_filename(urls, title, ext, output_dir, merge)
    output_filepath = os.path.join(output_dir, output_filename)

    if total_size:
        if not force and os.path.exists(output_filepath) and not auto_rename\
                and (os.path.getsize(output_filepath) >= total_size * 0.9\
                or skip_existing_file_size_check):
            if skip_existing_file_size_check:
                log.w('Skipping %s without checking size: file already exists' % output_filepath)
            else:
                log.w('Skipping %s: file already exists' % output_filepath)
            print()
            return
        bar = SimpleProgressBar(total_size, len(urls))
    else:
        bar = PiecesProgressBar(total_size, len(urls))

    if len(urls) == 1:
        url = urls[0]
        print('Downloading %s ...' % tr(output_filename))
        bar.update()
        url_save(
            url, output_filepath, bar, refer=refer, faker=faker,
            headers=headers, **kwargs
        )
        bar.done()
    else:
        parts = []
        print('Downloading %s ...' % tr(output_filename))
        bar.update()
        for i, url in enumerate(urls):
            output_filename_i = get_output_filename(urls, title, ext, output_dir, merge, part=i)
            output_filepath_i = os.path.join(output_dir, output_filename_i)
            parts.append(output_filepath_i)
            # print 'Downloading %s [%s/%s]...' % (tr(filename), i + 1, len(urls))
            bar.update_piece(i + 1)
            url_save(
                url, output_filepath_i, bar, refer=refer, is_part=True, faker=faker,
                headers=headers, **kwargs
            )
        bar.done()

        if not merge:
            print()
            return

        if 'av' in kwargs and kwargs['av']:
            from .processor.ffmpeg import has_ffmpeg_installed
            if has_ffmpeg_installed():
                from .processor.ffmpeg import ffmpeg_concat_av
                ret = ffmpeg_concat_av(parts, output_filepath, ext)
                print('Merged into %s' % output_filename)
                if ret == 0:
                    for part in parts:
                        os.remove(part)

        elif ext in ['flv', 'f4v']:
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_flv_to_mp4
                    ffmpeg_concat_flv_to_mp4(parts, output_filepath)
                else:
                    from .processor.join_flv import concat_flv
                    concat_flv(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'mp4':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_mp4_to_mp4
                    ffmpeg_concat_mp4_to_mp4(parts, output_filepath)
                else:
                    from .processor.join_mp4 import concat_mp4
                    concat_mp4(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'ts':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_ts_to_mkv
                    ffmpeg_concat_ts_to_mkv(parts, output_filepath)
                else:
                    from .processor.join_ts import concat_ts
                    concat_ts(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'mp3':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed

                assert has_ffmpeg_installed()
                from .processor.ffmpeg import ffmpeg_concat_mp3_to_mp3
                ffmpeg_concat_mp3_to_mp3(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        else:
            print("Can't merge %s files" % ext)

    print()