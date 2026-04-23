def save_files(js_data, images, do_make_zip, index):
    filenames = []
    fullfns = []
    parsed_infotexts = []

    # quick dictionary to class object conversion. Its necessary due apply_filename_pattern requiring it
    class MyObject:
        def __init__(self, d=None):
            if d is not None:
                for key, value in d.items():
                    setattr(self, key, value)

    data = json.loads(js_data)
    p = MyObject(data)

    path = shared.opts.outdir_save
    save_to_dirs = shared.opts.use_save_to_dirs_for_ui
    extension: str = shared.opts.samples_format
    start_index = 0

    if index > -1 and shared.opts.save_selected_only and (index >= data["index_of_first_image"]):  # ensures we are looking at a specific non-grid picture, and we have save_selected_only
        images = [images[index]]
        start_index = index

    os.makedirs(shared.opts.outdir_save, exist_ok=True)

    fields = [
        "prompt",
        "seed",
        "width",
        "height",
        "sampler",
        "cfgs",
        "steps",
        "filename",
        "negative_prompt",
        "sd_model_name",
        "sd_model_hash",
    ]
    logfile_path = os.path.join(shared.opts.outdir_save, "log.csv")

    # NOTE: ensure csv integrity when fields are added by
    # updating headers and padding with delimiters where needed
    if shared.opts.save_write_log_csv and os.path.exists(logfile_path):
        update_logfile(logfile_path, fields)

    with (open(logfile_path, "a", encoding="utf8", newline='') if shared.opts.save_write_log_csv else nullcontext()) as file:
        if file:
            at_start = file.tell() == 0
            writer = csv.writer(file)
            if at_start:
                writer.writerow(fields)

        for image_index, filedata in enumerate(images, start_index):
            image = image_from_url_text(filedata)

            is_grid = image_index < p.index_of_first_image

            p.batch_index = image_index-1

            parameters = parameters_copypaste.parse_generation_parameters(data["infotexts"][image_index], [])
            parsed_infotexts.append(parameters)
            fullfn, txt_fullfn = modules.images.save_image(image, path, "", seed=parameters['Seed'], prompt=parameters['Prompt'], extension=extension, info=p.infotexts[image_index], grid=is_grid, p=p, save_to_dirs=save_to_dirs)

            filename = os.path.relpath(fullfn, path)
            filenames.append(filename)
            fullfns.append(fullfn)
            if txt_fullfn:
                filenames.append(os.path.basename(txt_fullfn))
                fullfns.append(txt_fullfn)

        if file:
            writer.writerow([parsed_infotexts[0]['Prompt'], parsed_infotexts[0]['Seed'], data["width"], data["height"], data["sampler_name"], data["cfg_scale"], data["steps"], filenames[0], parsed_infotexts[0]['Negative prompt'], data["sd_model_name"], data["sd_model_hash"]])

    # Make Zip
    if do_make_zip:
        p.all_seeds = [parameters['Seed'] for parameters in parsed_infotexts]
        namegen = modules.images.FilenameGenerator(p, parsed_infotexts[0]['Seed'], parsed_infotexts[0]['Prompt'], image, True)
        zip_filename = namegen.apply(shared.opts.grid_zip_filename_pattern or "[datetime]_[[model_name]]_[seed]-[seed_last]")
        zip_filepath = os.path.join(path, f"{zip_filename}.zip")

        from zipfile import ZipFile
        with ZipFile(zip_filepath, "w") as zip_file:
            for i in range(len(fullfns)):
                with open(fullfns[i], mode="rb") as f:
                    zip_file.writestr(filenames[i], f.read())
        fullfns.insert(0, zip_filepath)

    return gr.File.update(value=fullfns, visible=True), plaintext_to_html(f"Saved: {filenames[0]}")