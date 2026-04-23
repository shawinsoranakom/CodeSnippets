def test_routing_rules_redirects(self, s3_bucket, aws_client, allow_bucket_acl):
        aws_client.s3.put_bucket_acl(Bucket=s3_bucket, ACL="public-read")
        aws_client.s3.put_bucket_website(
            Bucket=s3_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "error.html"},
                "RoutingRules": [
                    {
                        "Condition": {
                            "KeyPrefixEquals": "host/",
                        },
                        "Redirect": {"HostName": "random-hostname"},
                    },
                    {
                        "Condition": {
                            "KeyPrefixEquals": "replace-prefix/",
                        },
                        "Redirect": {"ReplaceKeyPrefixWith": "replaced-prefix/"},
                    },
                    {
                        "Condition": {
                            "KeyPrefixEquals": "protocol/",
                        },
                        "Redirect": {"Protocol": "https"},
                    },
                    {
                        "Condition": {
                            "KeyPrefixEquals": "code/",
                        },
                        "Redirect": {"HttpRedirectCode": "307"},
                    },
                ],
            },
        )

        website_url = _website_bucket_url(s3_bucket)

        response = requests.get(f"{website_url}/host/key", allow_redirects=False)
        assert response.status_code == 301
        assert response.headers["Location"] == "http://random-hostname/host/key"

        response = requests.get(f"{website_url}/replace-prefix/key", allow_redirects=False)
        assert response.status_code == 301
        assert response.headers["Location"] == f"{website_url}/replaced-prefix/key"

        response = requests.get(f"{website_url}/protocol/key", allow_redirects=False)
        assert response.status_code == 301
        assert not website_url.startswith("https")
        assert response.headers["Location"].startswith("https")

        response = requests.get(f"{website_url}/code/key", allow_redirects=False)
        assert response.status_code == 307