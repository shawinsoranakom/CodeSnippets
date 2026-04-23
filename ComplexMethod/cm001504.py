def image_from_url_text(filedata):
    if filedata is None:
        return None

    if type(filedata) == list and filedata and type(filedata[0]) == dict and filedata[0].get("is_file", False):
        filedata = filedata[0]

    if type(filedata) == dict and filedata.get("is_file", False):
        filename = filedata["name"]
        is_in_right_dir = ui_tempdir.check_tmp_file(shared.demo, filename)
        assert is_in_right_dir, 'trying to open image file outside of allowed directories'

        filename = filename.rsplit('?', 1)[0]
        return images.read(filename)

    if type(filedata) == list:
        if len(filedata) == 0:
            return None

        filedata = filedata[0]

    if filedata.startswith("data:image/png;base64,"):
        filedata = filedata[len("data:image/png;base64,"):]

    filedata = base64.decodebytes(filedata.encode('utf-8'))
    image = images.read(io.BytesIO(filedata))
    return image