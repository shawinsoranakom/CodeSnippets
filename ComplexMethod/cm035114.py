def convert_info_markdown(res, save_folder, img_name):
    """Save the recognition result as a markdown file.

    Args:
        res: Recognition result
        save_folder: Folder to save the markdown file
        img_name: PDF file or image file name

    Returns:
        None
    """

    def replace_special_char(content):
        special_chars = ["*", "`", "~", "$"]
        for char in special_chars:
            content = content.replace(char, "\\" + char)
        return content

    markdown_string = []

    for i, region in enumerate(res):
        if not region["res"] and region["type"].lower() != "figure":
            continue
        img_idx = region["img_idx"]

        if region["type"].lower() == "figure":
            img_file_name = "{}_{}.jpg".format(region["bbox"], img_idx)
            markdown_string.append(
                f"""<div align="center">\n\t<img src="{img_name+"/"+img_file_name}">\n</div>"""
            )
        elif region["type"].lower() == "title":
            markdown_string.append(
                f"""# {region['res'][0]['text']}"""
                + "".join(
                    [" " + one_region["text"] for one_region in region["res"][1:]]
                )
            )
        elif region["type"].lower() == "table":
            markdown_string.append(region["res"]["html"])
        elif region["type"].lower() == "header" or region["type"].lower() == "footer":
            pass
        elif region["type"].lower() == "equation" and "latex" in region["res"]:
            markdown_string.append(f"""$${region["res"]["latex"]}$$""")
        elif region["type"].lower() == "text":
            merge_func = check_merge_method(region)
            # logger.warning(f"use merge method:{merge_func.__name__}")
            markdown_string.append(replace_special_char(merge_func(region)))
        else:
            string = ""
            for line in region["res"]:
                string += line["text"] + " "
            markdown_string.append(string)

    md_path = os.path.join(save_folder, "{}_ocr.md".format(img_name))
    markdown_string = "\n\n".join(markdown_string)
    markdown_string = re.sub(r"\n{3,}", "\n\n", markdown_string)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_string)
    logger.info("markdown save to {}".format(md_path))