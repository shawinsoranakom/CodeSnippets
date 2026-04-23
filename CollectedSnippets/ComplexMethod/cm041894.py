def display_output_cli(output):
    if output["type"] == "console":
        print(output["content"])
    elif output["type"] == "image":
        if "base64" in output["format"]:
            if "." in output["format"]:
                extension = output["format"].split(".")[-1]
            else:
                extension = "png"
            with tempfile.NamedTemporaryFile(
                delete=False, suffix="." + extension
            ) as tmp_file:
                image_data = base64.b64decode(output["content"])
                tmp_file.write(image_data)

                # # Display in Terminal (DISABLED, i couldn't get it to work)
                # from term_image.image import from_file
                # image = from_file(tmp_file.name)
                # image.draw()

                open_file(tmp_file.name)
        elif output["format"] == "path":
            open_file(output["content"])
    elif "format" in output and output["format"] == "html":
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".html", mode="w"
        ) as tmp_file:
            html = output["content"]
            tmp_file.write(html)
            open_file(tmp_file.name)
    elif "format" in output and output["format"] == "javascript":
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".js", mode="w"
        ) as tmp_file:
            tmp_file.write(output["content"])
            open_file(tmp_file.name)