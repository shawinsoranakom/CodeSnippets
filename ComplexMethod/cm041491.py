def test_routing_rules_conditions(self, s3_bucket, aws_client, allow_bucket_acl):
        # https://github.com/localstack/localstack/issues/6308

        aws_client.s3.put_bucket_acl(Bucket=s3_bucket, ACL="public-read")
        aws_client.s3.put_bucket_website(
            Bucket=s3_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "error.html"},
                "RoutingRules": [
                    {
                        "Condition": {
                            "KeyPrefixEquals": "both-prefixed/",
                            "HttpErrorCodeReturnedEquals": "404",
                        },
                        "Redirect": {"ReplaceKeyWith": "redirected-both.html"},
                    },
                    {
                        "Condition": {"KeyPrefixEquals": "prefixed"},
                        "Redirect": {"ReplaceKeyWith": "redirected.html"},
                    },
                    {
                        "Condition": {"HttpErrorCodeReturnedEquals": "404"},
                        "Redirect": {"ReplaceKeyWith": "redirected.html"},
                    },
                ],
            },
        )

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="redirected.html",
            Body="redirected",
            ACL="public-read",
        )

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="prefixed-key-test",
            Body="prefixed",
            ACL="public-read",
        )

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="redirected-both.html",
            Body="redirected-both",
            ACL="public-read",
        )

        website_url = _website_bucket_url(s3_bucket)

        response = requests.get(f"{website_url}/non-existent-key", allow_redirects=False)
        assert response.status_code == 301
        assert response.headers["Location"] == f"{website_url}/redirected.html"

        # redirects when the custom ErrorDocument is not found
        response = requests.get(f"{website_url}/non-existent-key")
        assert response.status_code == 200
        assert response.text == "redirected"

        aws_client.s3.put_object(
            Bucket=s3_bucket,
            Key="error.html",
            Body="error",
            ACL="public-read",
        )

        response = requests.get(f"{website_url}/non-existent-key")
        assert response.status_code == 200
        assert response.text == "redirected"

        response = requests.get(f"{website_url}/prefixed-key-test")
        assert response.status_code == 200
        assert response.text == "redirected"

        response = requests.get(f"{website_url}/both-prefixed/")
        assert response.status_code == 200
        assert response.text == "redirected-both"