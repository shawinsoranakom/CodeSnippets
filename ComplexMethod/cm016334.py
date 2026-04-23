def is_intrested_file(
    file_path: str, interested_folders: list[str], platform: TestPlatform
) -> bool:
    ignored_patterns = ["cuda", "aten/gen_aten", "aten/aten_", "build/"]
    if any(pattern in file_path for pattern in ignored_patterns):
        return False

    # ignore files that are not belong to pytorch
    if platform == TestPlatform.OSS:
        # pyrefly: ignore [missing-import]
        from package.oss.utils import get_pytorch_folder

        if not file_path.startswith(get_pytorch_folder()):
            return False
    # if user has specified interested folder
    if interested_folders:
        for folder in interested_folders:
            intersted_folder_path = folder if folder.endswith("/") else f"{folder}/"
            if intersted_folder_path in file_path:
                return True
        return False
    else:
        return True