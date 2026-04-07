def get_img_path(path):
    return os.path.join(
        os.path.abspath(os.path.join(__file__, "..", "..")), "tests", path
    )