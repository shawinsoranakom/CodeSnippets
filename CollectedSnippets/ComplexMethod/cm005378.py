def add_model_to_auto_mappings(
    repo_path: Path,
    old_model_infos: ModelInfos,
    new_lowercase_name: str,
    new_model_paper_name: str,
    filenames_to_add: list[tuple[str, bool]],
):
    """
    Add a model to all the relevant mappings in the auto module.

    Args:
        old_model_infos (`ModelInfos`):
            The structure containing the class information of the old model.
        new_lowercase_name (`str`):
            The new lowercase model name.
        new_model_paper_name (`str`):
            The fully cased name (as in the official paper name) of the new model.
        filenames_to_add (`list[tuple[str, bool]]`):
            A list of tuples of all potential filenames to add for a new model, along a boolean flag describing if we
            should add this file or not. For example, [(`modeling_xxx.px`, True), (`configuration_xxx.py`, True), (`tokenization_xxx.py`, False),...]
    """
    new_cased_name = "".join(x.title() for x in new_lowercase_name.replace("-", "_").split("_"))
    old_lowercase_name = old_model_infos.lowercase_name
    old_cased_name = old_model_infos.camelcase_name
    filenames_to_add = [
        (filename.replace(old_lowercase_name, "auto"), to_add) for filename, to_add in filenames_to_add[1:]
    ]
    # fast tokenizer has the same auto mappings as normal ones
    corrected_filenames_to_add = []
    has_image_processor = has_video_processor = False
    for file, to_add in filenames_to_add:
        if "image_processing" in file:
            has_image_processor = True
        elif "video_processing" in file:
            has_video_processor = True
        elif re.search(r"(?:tokenization)|(?:image_processing)_auto_fast.py", file):
            previous_file, previous_to_add = corrected_filenames_to_add[-1]
            corrected_filenames_to_add[-1] = (previous_file, previous_to_add or to_add)
        else:
            corrected_filenames_to_add.append((file, to_add))

    # Add the config and image/video processor mappings directly as the handling is a bit different
    add_content_to_file(
        repo_path / "src" / "transformers" / "models" / "auto" / "auto_mappings.py",
        new_content=f'("{new_lowercase_name}", "{new_cased_name}Config"),\n        ',
        add_after="CONFIG_MAPPING_NAMES = OrderedDict(\n    [\n        ",
    )
    autofile = (repo_path / "src" / "transformers" / "models" / "auto" / "auto_mappings.py").read_text()
    if has_image_processor:
        matching_lines = re.findall(rf'^\s+\("{old_lowercase_name}",\s+{{[^}}]+}}\),?$', autofile, re.MULTILINE)
        if matching_lines:
            match = matching_lines[0]
            add_content_to_file(
                repo_path / "src" / "transformers" / "models" / "auto" / "auto_mappings.py",
                new_content=match.replace(old_lowercase_name, new_lowercase_name).replace(
                    old_cased_name, new_cased_name
                )
                + "\n",
                add_after="IMAGE_PROCESSOR_MAPPING_NAMES = OrderedDict(\n    [\n",
            )
    if has_video_processor:
        # Extract the VIDEO_PROCESSOR_MAPPING_NAMES block first
        block_match = re.search(
            r"VIDEO_PROCESSOR_MAPPING_NAMES\s*=\s*OrderedDict\(\s*\[(.*?)\]\s*\)", autofile, re.DOTALL
        )
        block = block_match.group(1)  # type: ignore
        matching_lines = re.findall(rf'^\s+\("{old_lowercase_name}",\s+"[^"]+"\),?$', block, re.MULTILINE)
        if matching_lines:
            match = matching_lines[0]
            add_content_to_file(
                repo_path / "src" / "transformers" / "models" / "auto" / "auto_mappings.py",
                new_content=match.replace(old_lowercase_name, new_lowercase_name).replace(
                    old_cased_name, new_cased_name
                )
                + "\n",
                add_after="VIDEO_PROCESSOR_MAPPING_NAMES = OrderedDict(\n    [\n",
            )

    for filename, to_add in corrected_filenames_to_add:
        if to_add:
            # The auto mapping
            filename = filename.replace("_fast.py", ".py")
            file = (repo_path / "src" / "transformers" / "models" / "auto" / filename).read_text()
            # The regex has to be a bit complex like this as the tokenizer mapping has new lines everywhere
            matching_lines = re.findall(
                rf'( {{8,12}}\(\s*"{old_lowercase_name}",.*?\),\n)(?: {{4,12}}\(|\])', file, re.DOTALL
            )
            for match in matching_lines:
                add_content_to_file(
                    repo_path / "src" / "transformers" / "models" / "auto" / filename,
                    new_content=match.replace(old_lowercase_name, new_lowercase_name).replace(
                        old_cased_name, new_cased_name
                    ),
                    add_after=match,
                )