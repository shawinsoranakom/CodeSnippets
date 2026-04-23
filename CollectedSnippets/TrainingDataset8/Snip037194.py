def get_video_files_in_dir(directory):
    out = []
    for item in os.listdir(directory):
        try:
            name, ext = item.split(".")
        except:
            continue
        if name and ext:
            if ext in VIDEO_EXTENSIONS:
                out.append(item)
    return out