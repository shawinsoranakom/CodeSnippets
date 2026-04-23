def export(test_list: TestList, platform_type: TestPlatform) -> None:
    print("start export")
    start_time = time.time()
    # find all merged profile under merged_folder and sub-folders
    g = os.walk(MERGED_FOLDER_BASE_DIR)
    for path, dir_list, file_list in g:
        # create corresponding merged folder in [json folder] if not exists yet
        create_corresponding_folder(
            path, MERGED_FOLDER_BASE_DIR, dir_list, JSON_FOLDER_BASE_DIR
        )
        # check if we can find merged profile under this path's folder
        for file_name in file_list:
            if file_name.endswith(".merged"):
                if not related_to_test_list(file_name, test_list):
                    continue
                print(f"start export {file_name}")
                # merged file
                merged_file = os.path.join(path, file_name)
                # json file
                json_file_name = replace_extension(file_name, ".json")
                json_file = os.path.join(
                    JSON_FOLDER_BASE_DIR,
                    convert_to_relative_path(path, MERGED_FOLDER_BASE_DIR),
                    json_file_name,
                )
                check_platform_type(platform_type)
                # binary file and shared library
                binary_file = ""
                shared_library_list = []
                if platform_type == TestPlatform.FBCODE:
                    from caffe2.fb.code_coverage.tool.package.fbcode.utils import (  # type: ignore[import]
                        get_fbcode_binary_folder,
                    )

                    binary_file = os.path.join(
                        get_fbcode_binary_folder(path),
                        get_test_name_from_whole_path(merged_file),
                    )
                elif platform_type == TestPlatform.OSS:
                    from ..oss.utils import get_oss_binary_file, get_oss_shared_library

                    test_name = get_test_name_from_whole_path(merged_file)
                    # if it is python test, no need to provide binary, shared library is enough
                    binary_file = (
                        ""
                        if test_name.endswith(".py")
                        else get_oss_binary_file(test_name, TestType.CPP)
                    )
                    shared_library_list = get_oss_shared_library()
                export_target(
                    merged_file,
                    json_file,
                    binary_file,
                    shared_library_list,
                    platform_type,
                )
    print_time("export take time: ", start_time, summary_time=True)