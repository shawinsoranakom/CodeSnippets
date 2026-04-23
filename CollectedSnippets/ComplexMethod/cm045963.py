def create_result_zip(
    output_dir: str,
    pdf_file_names: list[str],
    backend: str,
    parse_method: str,
    return_md: bool,
    return_middle_json: bool,
    return_model_output: bool,
    return_content_list: bool,
    return_images: bool,
    return_original_file: bool,
) -> str:
    zip_fd, zip_path = tempfile.mkstemp(suffix=".zip", prefix="mineru_results_")
    os.close(zip_fd)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for pdf_name in pdf_file_names:
            try:
                parse_dir = get_parse_dir(output_dir, pdf_name, backend, parse_method)
            except ValueError:
                logger.warning(f"Unknown backend type: {backend}, skipping {pdf_name}")
                continue

            if not os.path.exists(parse_dir):
                continue

            if return_md:
                path = os.path.join(parse_dir, f"{pdf_name}.md")
                if os.path.exists(path):
                    zf.write(
                        path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            f"{pdf_name}.md",
                        ),
                    )

            if return_middle_json:
                path = os.path.join(parse_dir, f"{pdf_name}_middle.json")
                if os.path.exists(path):
                    zf.write(
                        path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            f"{pdf_name}_middle.json",
                        ),
                    )

            if return_model_output:
                path = os.path.join(parse_dir, f"{pdf_name}_model.json")
                if os.path.exists(path):
                    zf.write(
                        path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            f"{pdf_name}_model.json",
                        ),
                    )

            if return_content_list:
                path = os.path.join(parse_dir, f"{pdf_name}_content_list.json")
                if os.path.exists(path):
                    zf.write(
                        path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            f"{pdf_name}_content_list.json",
                        ),
                    )

                path = os.path.join(parse_dir, f"{pdf_name}_content_list_v2.json")
                if os.path.exists(path):
                    zf.write(
                        path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            f"{pdf_name}_content_list_v2.json",
                        ),
                    )

            if return_images:
                images_dir = os.path.join(parse_dir, "images")
                image_paths = get_images_dir_image_paths(images_dir)
                for image_path in image_paths:
                    zf.write(
                        image_path,
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            os.path.join("images", os.path.basename(image_path)),
                        ),
                    )

            if return_original_file:
                origin_pattern = f"{pdf_name}_origin."
                for path in sorted(Path(parse_dir).iterdir()):
                    if not path.is_file():
                        continue
                    if not path.name.startswith(origin_pattern):
                        continue
                    zf.write(
                        str(path),
                        arcname=build_zip_arcname(
                            pdf_name,
                            parse_dir,
                            path.name,
                        ),
                    )
    return zip_path