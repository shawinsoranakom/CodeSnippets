def test_persist(self):
        uri = os.environ.get("GCS_TEST_FILE_URI")
        if not uri:
            pytest.skip("No GCS URI available for testing")
        data = b"TestGCSFilesStore: \xe2\x98\x83"
        buf = BytesIO(data)
        meta = {"foo": "bar"}
        path = "full/filename"
        store = GCSFilesStore(uri)
        store.POLICY = "authenticatedRead"
        expected_policy = {"role": "READER", "entity": "allAuthenticatedUsers"}
        yield store.persist_file(path, buf, info=None, meta=meta, headers=None)
        s = yield store.stat_file(path, info=None)
        assert "last_modified" in s
        assert "checksum" in s
        assert s["checksum"] == "cdcda85605e46d0af6110752770dce3c"
        u = urlparse(uri)
        content, acl, blob = get_gcs_content_and_delete(u.hostname, u.path[1:] + path)
        assert content == data
        assert blob.metadata == {"foo": "bar"}
        assert blob.cache_control == GCSFilesStore.CACHE_CONTROL
        assert blob.content_type == "application/octet-stream"
        assert expected_policy in acl