def fixture(filename):
        path = os.path.join(str(tmpdir), filename)

        def reset(path):
            os.mkdir('d')
            with tarfile.TarFile(path, 'w') as archive:
                for file in ('a', 'b', 'c', 'd/e'):
                    with open(file, 'w') as f:
                        f.write('*')

                    archive.add(file)

                    os.remove(file)

            with tarfile.TarFile(path, 'r') as archive:
                archive.extractall()

        os.chdir(str(tmpdir))
        reset(path)

        assert set(os.listdir('.')) == {filename, 'a', 'b', 'c', 'd'}
        assert set(os.listdir('./d')) == {'e'}