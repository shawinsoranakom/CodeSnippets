def get_postprocessors(opts):
    yield from opts.add_postprocessors

    for when, actions in opts.parse_metadata.items():
        yield {
            'key': 'MetadataParser',
            'actions': actions,
            'when': when,
        }
    sponsorblock_query = opts.sponsorblock_mark | opts.sponsorblock_remove
    if sponsorblock_query:
        yield {
            'key': 'SponsorBlock',
            'categories': sponsorblock_query,
            'api': opts.sponsorblock_api,
            'when': 'after_filter',
        }
    if opts.convertsubtitles:
        yield {
            'key': 'FFmpegSubtitlesConvertor',
            'format': opts.convertsubtitles,
            'when': 'before_dl',
        }
    if opts.convertthumbnails:
        yield {
            'key': 'FFmpegThumbnailsConvertor',
            'format': opts.convertthumbnails,
            'when': 'before_dl',
        }
    if opts.extractaudio:
        yield {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': opts.audioformat,
            'preferredquality': opts.audioquality,
            'nopostoverwrites': opts.nopostoverwrites,
        }
    if opts.remuxvideo:
        yield {
            'key': 'FFmpegVideoRemuxer',
            'preferedformat': opts.remuxvideo,
        }
    if opts.recodevideo:
        yield {
            'key': 'FFmpegVideoConvertor',
            'preferedformat': opts.recodevideo,
        }
    # If ModifyChapters is going to remove chapters, subtitles must already be in the container.
    if opts.embedsubtitles:
        keep_subs = 'no-keep-subs' not in opts.compat_opts
        yield {
            'key': 'FFmpegEmbedSubtitle',
            # already_have_subtitle = True prevents the file from being deleted after embedding
            'already_have_subtitle': opts.writesubtitles and keep_subs,
        }
        if not opts.writeautomaticsub and keep_subs:
            opts.writesubtitles = True

    # ModifyChapters must run before FFmpegMetadataPP
    if opts.remove_chapters or sponsorblock_query:
        yield {
            'key': 'ModifyChapters',
            'remove_chapters_patterns': opts.remove_chapters,
            'remove_sponsor_segments': opts.sponsorblock_remove,
            'remove_ranges': opts.remove_ranges,
            'sponsorblock_chapter_title': opts.sponsorblock_chapter_title,
            'force_keyframes': opts.force_keyframes_at_cuts,
        }
    # FFmpegMetadataPP should be run after FFmpegVideoConvertorPP and
    # FFmpegExtractAudioPP as containers before conversion may not support
    # metadata (3gp, webm, etc.)
    # By default ffmpeg preserves metadata applicable for both
    # source and target containers. From this point the container won't change,
    # so metadata can be added here.
    if opts.addmetadata or opts.addchapters or opts.embed_infojson:
        yield {
            'key': 'FFmpegMetadata',
            'add_chapters': opts.addchapters,
            'add_metadata': opts.addmetadata,
            'add_infojson': opts.embed_infojson,
        }
    if opts.embedthumbnail:
        yield {
            'key': 'EmbedThumbnail',
            # already_have_thumbnail = True prevents the file from being deleted after embedding
            'already_have_thumbnail': opts.writethumbnail,
        }
        if not opts.writethumbnail:
            opts.writethumbnail = True
            opts.outtmpl['pl_thumbnail'] = ''
    if opts.split_chapters:
        yield {
            'key': 'FFmpegSplitChapters',
            'force_keyframes': opts.force_keyframes_at_cuts,
        }
    # XAttrMetadataPP should be run after post-processors that may change file contents
    if opts.xattrs:
        yield {'key': 'XAttrMetadata'}
    if opts.concat_playlist != 'never':
        yield {
            'key': 'FFmpegConcat',
            'only_multi_video': opts.concat_playlist != 'always',
            'when': 'playlist',
        }
    # Exec must be the last PP of each category
    for when, exec_cmd in opts.exec_cmd.items():
        yield {
            'key': 'Exec',
            'exec_cmd': exec_cmd,
            'when': when,
        }