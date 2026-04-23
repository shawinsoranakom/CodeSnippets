def test_collection_build(collection_artifact):
    tar_path = os.path.join(collection_artifact, 'ansible_test-build_collection-1.0.0.tar.gz')
    assert tarfile.is_tarfile(tar_path)

    with tarfile.open(tar_path, mode='r') as tar:
        tar_members = tar.getmembers()

        valid_files = ['MANIFEST.json', 'FILES.json', 'roles', 'docs', 'plugins', 'plugins/README.md', 'README.md',
                       'runme.sh', 'meta', 'meta/runtime.yml']
        assert len(tar_members) == len(valid_files)

        # Verify the uid and gid is 0 and the correct perms are set
        for member in tar_members:
            assert member.name in valid_files

            assert member.gid == 0
            assert member.gname == ''
            assert member.uid == 0
            assert member.uname == ''
            if member.isdir() or member.name == 'runme.sh':
                assert member.mode == S_IRWXU_RXG_RXO
            else:
                assert member.mode == S_IRWU_RG_RO

        manifest_file = tar.extractfile(tar_members[0])
        try:
            manifest = json.loads(to_text(manifest_file.read()))
        finally:
            manifest_file.close()

        coll_info = manifest['collection_info']
        file_manifest = manifest['file_manifest_file']
        assert manifest['format'] == 1
        assert len(manifest.keys()) == 3

        assert coll_info['namespace'] == 'ansible_test'
        assert coll_info['name'] == 'build_collection'
        assert coll_info['version'] == '1.0.0'
        assert coll_info['authors'] == ['your name <example@domain.com>']
        assert coll_info['readme'] == 'README.md'
        assert coll_info['tags'] == []
        assert coll_info['description'] == 'your collection description'
        assert coll_info['license'] == ['GPL-2.0-or-later']
        assert coll_info['license_file'] is None
        assert coll_info['dependencies'] == {}
        assert coll_info['repository'] == 'http://example.com/repository'
        assert coll_info['documentation'] == 'http://docs.example.com'
        assert coll_info['homepage'] == 'http://example.com'
        assert coll_info['issues'] == 'http://example.com/issue/tracker'
        assert len(coll_info.keys()) == 14

        assert file_manifest['name'] == 'FILES.json'
        assert file_manifest['ftype'] == 'file'
        assert file_manifest['chksum_type'] == 'sha256'
        assert file_manifest['chksum_sha256'] is not None  # Order of keys makes it hard to verify the checksum
        assert file_manifest['format'] == 1
        assert len(file_manifest.keys()) == 5

        files_file = tar.extractfile(tar_members[1])
        try:
            files = json.loads(to_text(files_file.read()))
        finally:
            files_file.close()

        assert len(files['files']) == 9
        assert files['format'] == 1
        assert len(files.keys()) == 2

        valid_files_entries = ['.', 'roles', 'docs', 'plugins', 'plugins/README.md', 'README.md', 'runme.sh', 'meta', 'meta/runtime.yml']
        for file_entry in files['files']:
            assert file_entry['name'] in valid_files_entries
            assert file_entry['format'] == 1

            if file_entry['name'] in ['plugins/README.md', 'runme.sh', 'meta/runtime.yml']:
                assert file_entry['ftype'] == 'file'
                assert file_entry['chksum_type'] == 'sha256'
                # Can't test the actual checksum as the html link changes based on the version or the file contents
                # don't matter
                assert file_entry['chksum_sha256'] is not None
            elif file_entry['name'] == 'README.md':
                assert file_entry['ftype'] == 'file'
                assert file_entry['chksum_type'] == 'sha256'
                assert file_entry['chksum_sha256'] == '6d8b5f9b5d53d346a8cd7638a0ec26e75e8d9773d952162779a49d25da6ef4f5'
            else:
                assert file_entry['ftype'] == 'dir'
                assert file_entry['chksum_type'] is None
                assert file_entry['chksum_sha256'] is None

            assert len(file_entry.keys()) == 5