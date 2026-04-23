def test_build_with_existing_files_and_manifest(collection_input):
    input_dir, output_dir = collection_input

    with open(os.path.join(input_dir, 'MANIFEST.json'), "wb") as fd:
        fd.write(b'{"collection_info": {"version": "6.6.6"}, "version": 1}')

    with open(os.path.join(input_dir, 'FILES.json'), "wb") as fd:
        fd.write(b'{"files": [], "format": 1}')

    with open(os.path.join(input_dir, "plugins", "MANIFEST.json"), "wb") as fd:
        fd.write(b"test data that should be in build")

    collection.build_collection(to_text(input_dir, errors='surrogate_or_strict'), to_text(output_dir, errors='surrogate_or_strict'), False)

    output_artifact = os.path.join(output_dir, 'ansible_namespace-collection-0.1.0.tar.gz')
    assert tarfile.is_tarfile(output_artifact)

    with tarfile.open(output_artifact, mode='r') as actual:
        members = actual.getmembers()

        manifest_file = [m for m in members if m.path == "MANIFEST.json"][0]
        manifest_file_obj = actual.extractfile(manifest_file.name)
        manifest_file_text = manifest_file_obj.read()
        manifest_file_obj.close()
        assert manifest_file_text != b'{"collection_info": {"version": "6.6.6"}, "version": 1}'

        json_file = [m for m in members if m.path == "MANIFEST.json"][0]
        json_file_obj = actual.extractfile(json_file.name)
        json_file_text = json_file_obj.read()
        json_file_obj.close()
        assert json_file_text != b'{"files": [], "format": 1}'

        sub_manifest_file = [m for m in members if m.path == "plugins/MANIFEST.json"][0]
        sub_manifest_file_obj = actual.extractfile(sub_manifest_file.name)
        sub_manifest_file_text = sub_manifest_file_obj.read()
        sub_manifest_file_obj.close()
        assert sub_manifest_file_text == b"test data that should be in build"