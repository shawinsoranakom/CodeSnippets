def update_file_writer_config(config: Dict, args: Namespace):
    file_writer_config = config.file_writer
    file_writer_config.update(
        write_to_movie=(not args.skip_animations and args.write_file),
        subdivide_output=args.subdivide,
        save_last_frame=(args.skip_animations and args.write_file),
        png_mode=("RGBA" if args.transparent else "RGB"),
        movie_file_extension=(get_file_ext(args)),
        output_directory=get_output_directory(args, config),
        file_name=args.file_name,
        open_file_upon_completion=args.open,
        show_file_location_upon_completion=args.finder,
        quiet=args.quiet,
    )

    if args.vcodec:
        file_writer_config.video_codec = args.vcodec
    elif args.transparent:
        file_writer_config.video_codec = 'prores_ks'
        file_writer_config.pixel_format = ''
    elif args.gif:
        file_writer_config.video_codec = ''

    if args.pix_fmt:
        file_writer_config.pixel_format = args.pix_fmt