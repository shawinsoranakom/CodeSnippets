def test_website_hosting_index_lookup(self, s3_bucket, snapshot, aws_client, allow_bucket_acl):
        snapshot.add_transformers_list(self._get_static_hosting_transformers(snapshot))

        aws_client.s3.put_bucket_acl(Bucket=s3_bucket, ACL="public-read")
        aws_client.s3.put_bucket_website(
            Bucket=s3_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
            },
        )

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="index.html",
            Body="index",
            ContentType="text/html",
            ACL="public-read",
        )

        website_url = _website_bucket_url(s3_bucket)
        # actual key
        response = requests.get(website_url)
        assert response.status_code == 200
        assert response.text == "index"

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="directory/index.html",
            Body="index",
            ContentType="text/html",
            ACL="public-read",
        )

        response = requests.get(f"{website_url}/directory", allow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "/directory/"

        response = requests.get(f"{website_url}/directory/", verify=False)
        assert response.status_code == 200
        assert response.text == "index"

        response = requests.get(f"{website_url}/directory-wrong", verify=False)
        assert response.status_code == 404
        snapshot.match("404-no-trailing-slash", response.text)

        response = requests.get(f"{website_url}/directory-wrong/", verify=False)
        assert response.status_code == 404
        snapshot.match("404-with-trailing-slash", response.text)