def test_s3_static_website_hosting(self, s3_bucket, aws_client, allow_bucket_acl):
        aws_client.s3.put_bucket_acl(Bucket=s3_bucket, ACL="public-read")
        index_obj = aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="test/index.html",
            Body="index",
            ContentType="text/html",
            ACL="public-read",
        )
        error_obj = aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="test/error.html",
            Body="error",
            ContentType="text/html",
            ACL="public-read",
        )
        actual_key_obj = aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="actual/key.html",
            Body="key",
            ContentType="text/html",
            ACL="public-read",
        )
        with_content_type_obj = aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="with-content-type/key.js",
            Body="some js",
            ContentType="application/javascript; charset=utf-8",
            ACL="public-read",
        )
        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="to-be-redirected.html",
            WebsiteRedirectLocation="/actual/key.html",
            ACL="public-read",
        )
        aws_client.s3.put_bucket_website(
            Bucket=s3_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "test/error.html"},
            },
        )
        website_url = _website_bucket_url(s3_bucket)
        # actual key
        url = f"{website_url}/actual/key.html"
        response = requests.get(url, verify=False)
        assert response.status_code == 200
        assert response.text == "key"
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "text/html"
        assert "etag" in response.headers
        assert actual_key_obj["ETag"] in response.headers["etag"]

        # If-None-Match and Etag
        response = requests.get(
            url, headers={"If-None-Match": actual_key_obj["ETag"]}, verify=False
        )
        assert response.status_code == 304

        # key with specified content-type
        url = f"{website_url}/with-content-type/key.js"
        response = requests.get(url, verify=False)
        assert response.status_code == 200
        assert response.text == "some js"
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/javascript; charset=utf-8"
        assert "etag" in response.headers
        assert response.headers["etag"] == with_content_type_obj["ETag"]

        # index document
        url = f"{website_url}/test"
        response = requests.get(url, verify=False)
        assert response.status_code == 200
        assert response.text == "index"
        assert "content-type" in response.headers
        assert "text/html" in response.headers["content-type"]
        assert "etag" in response.headers
        assert response.headers["etag"] == index_obj["ETag"]

        # root path test
        url = f"{website_url}/"
        response = requests.get(url, verify=False)
        assert response.status_code == 404
        assert response.text == "error"
        assert "content-type" in response.headers
        assert "text/html" in response.headers["content-type"]
        assert "etag" in response.headers
        assert response.headers["etag"] == error_obj["ETag"]

        # error document
        url = f"{website_url}/something"
        response = requests.get(url, verify=False)
        assert response.status_code == 404
        assert response.text == "error"
        assert "content-type" in response.headers
        assert "text/html" in response.headers["content-type"]
        assert "etag" in response.headers
        assert response.headers["etag"] == error_obj["ETag"]

        # redirect object
        url = f"{website_url}/to-be-redirected.html"
        response = requests.get(url, verify=False, allow_redirects=False)
        assert response.status_code == 301
        assert "location" in response.headers
        assert "actual/key.html" in response.headers["location"]

        response = requests.get(url, verify=False)
        assert response.status_code == 200
        assert response.headers["etag"] == actual_key_obj["ETag"]