def test_s3_query_args_routing():
    router = RestServiceOperationRouter(load_service("s3"))

    op, params = router.match(Request("DELETE", "/mybucket?delete"))
    assert op.name == "DeleteBucket"
    assert params == {"Bucket": "mybucket"}

    op, params = router.match(Request("DELETE", "/mybucket/?delete"))
    assert op.name == "DeleteBucket"
    assert params == {"Bucket": "mybucket"}

    op, params = router.match(Request("DELETE", "/mybucket/mykey?delete"))
    assert op.name == "DeleteObject"
    assert params == {"Bucket": "mybucket", "Key": "mykey"}

    op, params = router.match(Request("DELETE", "/mybucket/mykey/?delete"))
    assert op.name == "DeleteObject"
    assert params == {"Bucket": "mybucket", "Key": "mykey"}