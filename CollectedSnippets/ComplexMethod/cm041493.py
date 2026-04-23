def test_routing_rules_empty_replace_prefix(self, s3_bucket, aws_client, allow_bucket_acl):
        aws_client.s3.put_bucket_acl(Bucket=s3_bucket, ACL="public-read")
        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="index.html",
            Body="index",
            ACL="public-read",
        )
        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="test.html",
            Body="test",
            ACL="public-read",
        )
        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="error.html",
            Body="error",
            ACL="public-read",
        )
        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="mydocs/test.html",
            Body="mydocs",
            ACL="public-read",
        )

        # change configuration
        aws_client.s3.put_bucket_website(
            Bucket=s3_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "error.html"},
                "RoutingRules": [
                    {
                        "Condition": {"KeyPrefixEquals": "docs/"},
                        "Redirect": {"ReplaceKeyPrefixWith": ""},
                    },
                    {
                        "Condition": {"KeyPrefixEquals": "another/path/"},
                        "Redirect": {"ReplaceKeyPrefixWith": ""},
                    },
                ],
            },
        )

        website_url = _website_bucket_url(s3_bucket)

        # testing that routing rule redirect correctly (by removing the defined prefix)
        response = requests.get(f"{website_url}/docs/test.html")
        assert response.status_code == 200
        assert response.text == "test"

        response = requests.get(f"{website_url}/another/path/test.html")
        assert response.status_code == 200
        assert response.text == "test"

        response = requests.get(f"{website_url}/docs/mydocs/test.html")
        assert response.status_code == 200
        assert response.text == "mydocs"

        # no routing rule defined -> should result in error
        response = requests.get(f"{website_url}/docs2/test.html")
        assert response.status_code == 404
        assert response.text == "error"