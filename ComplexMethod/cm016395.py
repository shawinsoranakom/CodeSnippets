def test_walk_directory(temp_directory):
    result: List[FileSystemItem] = FileSystemOperations.walk_directory(str(temp_directory))

    assert len(result) == 5  # 2 directories and 3 files

    files = [item for item in result if item['type'] == 'file']
    dirs = [item for item in result if item['type'] == 'directory']

    assert len(files) == 3
    assert len(dirs) == 2

    file_names = {file['name'] for file in files}
    assert file_names == {'file1.txt', 'file2.txt', 'file3.txt'}

    dir_names = {dir['name'] for dir in dirs}
    assert dir_names == {'dir1', 'dir2'}