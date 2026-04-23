def build_result_dict(
    output_dir: str,
    pdf_file_names: list[str],
    backend: str,
    parse_method: str,
    return_md: bool,
    return_middle_json: bool,
    return_model_output: bool,
    return_content_list: bool,
    return_images: bool,
) -> dict[str, dict[str, Any]]:
    result_dict: dict[str, dict[str, Any]] = {}
    for pdf_name in pdf_file_names:
        result_dict[pdf_name] = {}
        data = result_dict[pdf_name]

        try:
            parse_dir = get_parse_dir(output_dir, pdf_name, backend, parse_method)
        except ValueError:
            logger.warning(f"Unknown backend type: {backend}, skipping {pdf_name}")
            continue

        if not os.path.exists(parse_dir):
            continue

        if return_md:
            data["md_content"] = get_infer_result(".md", pdf_name, parse_dir)
        if return_middle_json:
            data["middle_json"] = get_infer_result("_middle.json", pdf_name, parse_dir)
        if return_model_output:
            data["model_output"] = get_infer_result("_model.json", pdf_name, parse_dir)
        if return_content_list:
            data["content_list"] = get_infer_result(
                "_content_list.json", pdf_name, parse_dir
            )
        if return_images:
            images_dir = os.path.join(parse_dir, "images")
            image_paths = get_images_dir_image_paths(images_dir)
            data["images"] = {
                os.path.basename(
                    image_path
                ): f"data:{get_image_mime_type(image_path)};base64,{encode_image(image_path)}"
                for image_path in image_paths
            }
    return result_dict