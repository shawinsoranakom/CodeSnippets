def test_get_image_paths(tmp_path: str) -> None:
    """ Unit test for :func:`~lib.utils.test_get_image_paths`

    Parameters
    ----------
    tmp_path: str
        pytest temporary path to generate folders
    """
    # Test getting image paths from a folder with no images
    test_folder = os.path.join(tmp_path, "test_image_folder")
    os.makedirs(test_folder)
    assert not get_image_paths(test_folder)

    # Populate 2 different image files and 1 text file
    test_jpg_path = os.path.join(test_folder, "test_image.jpg")
    test_png_path = os.path.join(test_folder, "test_image.png")
    test_txt_path = os.path.join(test_folder, "test_file.txt")
    for fname in (test_jpg_path, test_png_path, test_txt_path):
        with open(fname, "a", encoding="utf-8"):
            pass

    # Test getting any image paths from a folder with images and random files
    exists = [os.path.join(test_folder, img)
              for img in os.listdir(test_folder) if os.path.splitext(img)[-1] != ".txt"]
    assert sorted(get_image_paths(test_folder)) == sorted(exists)

    # Test getting image paths from a folder with images with a specific extension
    exists = [os.path.join(test_folder, img)
              for img in os.listdir(test_folder) if os.path.splitext(img)[-1] == ".png"]
    assert sorted(get_image_paths(test_folder, extension=".png")) == sorted(exists)