def zip_error(tmpdir):
    def zip_error_inner(filename):
        path = os.path.join(str(tmpdir), filename)

        def reset(path):
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('a', '1')
                archive.writestr('b', '2')
                archive.writestr('c', '3')

                archive.writestr('d/e', '4')

                archive.extractall()

        os.chdir(str(tmpdir))
        reset(path)

        dir_list = os.listdir(u'.')
        if filename not in dir_list:
            filename = normalize('NFD', filename)

        assert set(dir_list) == {filename, 'a', 'b', 'c', 'd'}
        assert set(os.listdir('./d')) == {'e'}
    return zip_error_inner