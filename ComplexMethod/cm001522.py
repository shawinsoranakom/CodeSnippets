def save_image(image, path, basename, seed=None, prompt=None, extension='png', info=None, short_filename=False, no_prompt=False, grid=False, pnginfo_section_name='parameters', p=None, existing_info=None, forced_filename=None, suffix="", save_to_dirs=None):
    """Save an image.

    Args:
        image (`PIL.Image`):
            The image to be saved.
        path (`str`):
            The directory to save the image. Note, the option `save_to_dirs` will make the image to be saved into a sub directory.
        basename (`str`):
            The base filename which will be applied to `filename pattern`.
        seed, prompt, short_filename,
        extension (`str`):
            Image file extension, default is `png`.
        pngsectionname (`str`):
            Specify the name of the section which `info` will be saved in.
        info (`str` or `PngImagePlugin.iTXt`):
            PNG info chunks.
        existing_info (`dict`):
            Additional PNG info. `existing_info == {pngsectionname: info, ...}`
        no_prompt:
            TODO I don't know its meaning.
        p (`StableDiffusionProcessing`)
        forced_filename (`str`):
            If specified, `basename` and filename pattern will be ignored.
        save_to_dirs (bool):
            If true, the image will be saved into a subdirectory of `path`.

    Returns: (fullfn, txt_fullfn)
        fullfn (`str`):
            The full path of the saved imaged.
        txt_fullfn (`str` or None):
            If a text file is saved for this image, this will be its full path. Otherwise None.
    """
    namegen = FilenameGenerator(p, seed, prompt, image, basename=basename)

    # WebP and JPG formats have maximum dimension limits of 16383 and 65535 respectively. switch to PNG which has a much higher limit
    if (image.height > 65535 or image.width > 65535) and extension.lower() in ("jpg", "jpeg") or (image.height > 16383 or image.width > 16383) and extension.lower() == "webp":
        print('Image dimensions too large; saving as PNG')
        extension = "png"

    if save_to_dirs is None:
        save_to_dirs = (grid and opts.grid_save_to_dirs) or (not grid and opts.save_to_dirs and not no_prompt)

    if save_to_dirs:
        dirname = namegen.apply(opts.directories_filename_pattern or "[prompt_words]").lstrip(' ').rstrip('\\ /')
        path = os.path.join(path, dirname)

    os.makedirs(path, exist_ok=True)

    if forced_filename is None:
        if short_filename or seed is None:
            file_decoration = ""
        elif opts.save_to_dirs:
            file_decoration = opts.samples_filename_pattern or "[seed]"
        else:
            file_decoration = opts.samples_filename_pattern or "[seed]-[prompt_spaces]"

        file_decoration = namegen.apply(file_decoration) + suffix

        add_number = opts.save_images_add_number or file_decoration == ''

        if file_decoration != "" and add_number:
            file_decoration = f"-{file_decoration}"

        if add_number:
            basecount = get_next_sequence_number(path, basename)
            fullfn = None
            for i in range(500):
                fn = f"{basecount + i:05}" if basename == '' else f"{basename}-{basecount + i:04}"
                fullfn = os.path.join(path, f"{fn}{file_decoration}.{extension}")
                if not os.path.exists(fullfn):
                    break
        else:
            fullfn = os.path.join(path, f"{file_decoration}.{extension}")
    else:
        fullfn = os.path.join(path, f"{forced_filename}.{extension}")

    pnginfo = existing_info or {}
    if info is not None:
        pnginfo[pnginfo_section_name] = info

    params = script_callbacks.ImageSaveParams(image, p, fullfn, pnginfo)
    script_callbacks.before_image_saved_callback(params)

    image = params.image
    fullfn = params.filename
    info = params.pnginfo.get(pnginfo_section_name, None)

    def _atomically_save_image(image_to_save, filename_without_extension, extension):
        """
        save image with .tmp extension to avoid race condition when another process detects new image in the directory
        """
        temp_file_path = f"{filename_without_extension}.tmp"

        save_image_with_geninfo(image_to_save, info, temp_file_path, extension, existing_pnginfo=params.pnginfo, pnginfo_section_name=pnginfo_section_name)

        filename = filename_without_extension + extension
        if shared.opts.save_images_replace_action != "Replace":
            n = 0
            while os.path.exists(filename):
                n += 1
                filename = f"{filename_without_extension}-{n}{extension}"
        os.replace(temp_file_path, filename)

    fullfn_without_extension, extension = os.path.splitext(params.filename)
    if hasattr(os, 'statvfs'):
        max_name_len = os.statvfs(path).f_namemax
        fullfn_without_extension = fullfn_without_extension[:max_name_len - max(4, len(extension))]
        params.filename = fullfn_without_extension + extension
        fullfn = params.filename
    _atomically_save_image(image, fullfn_without_extension, extension)

    image.already_saved_as = fullfn

    oversize = image.width > opts.target_side_length or image.height > opts.target_side_length
    if opts.export_for_4chan and (oversize or os.stat(fullfn).st_size > opts.img_downscale_threshold * 1024 * 1024):
        ratio = image.width / image.height
        resize_to = None
        if oversize and ratio > 1:
            resize_to = round(opts.target_side_length), round(image.height * opts.target_side_length / image.width)
        elif oversize:
            resize_to = round(image.width * opts.target_side_length / image.height), round(opts.target_side_length)

        if resize_to is not None:
            try:
                # Resizing image with LANCZOS could throw an exception if e.g. image mode is I;16
                image = image.resize(resize_to, LANCZOS)
            except Exception:
                image = image.resize(resize_to)
        try:
            _atomically_save_image(image, fullfn_without_extension, ".jpg")
        except Exception as e:
            errors.display(e, "saving image as downscaled JPG")

    if opts.save_txt and info is not None:
        txt_fullfn = f"{fullfn_without_extension}.txt"
        with open(txt_fullfn, "w", encoding="utf8") as file:
            file.write(f"{info}\n")
    else:
        txt_fullfn = None

    script_callbacks.image_saved_callback(params)

    return fullfn, txt_fullfn