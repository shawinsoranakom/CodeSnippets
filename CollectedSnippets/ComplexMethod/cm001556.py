def save_pil_to_file(self, pil_image, dir=None, format="png"):
    already_saved_as = getattr(pil_image, 'already_saved_as', None)
    if already_saved_as and os.path.isfile(already_saved_as):
        register_tmp_file(shared.demo, already_saved_as)
        filename_with_mtime = f'{already_saved_as}?{os.path.getmtime(already_saved_as)}'
        register_tmp_file(shared.demo, filename_with_mtime)
        return filename_with_mtime

    if shared.opts.temp_dir != "":
        dir = shared.opts.temp_dir
    else:
        os.makedirs(dir, exist_ok=True)

    use_metadata = False
    metadata = PngImagePlugin.PngInfo()
    for key, value in pil_image.info.items():
        if isinstance(key, str) and isinstance(value, str):
            metadata.add_text(key, value)
            use_metadata = True

    file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir=dir)
    pil_image.save(file_obj, pnginfo=(metadata if use_metadata else None))
    return file_obj.name