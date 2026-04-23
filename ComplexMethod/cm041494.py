def test_website_hosting_redirect_all(self, s3_create_bucket, aws_client):
        bucket_name_redirected = f"bucket-{short_uid()}"
        bucket_name = f"bucket-{short_uid()}"

        s3_create_bucket(Bucket=bucket_name_redirected)
        aws_client.s3.delete_bucket_ownership_controls(Bucket=bucket_name_redirected)
        aws_client.s3.delete_public_access_block(Bucket=bucket_name_redirected)
        aws_client.s3.put_bucket_acl(Bucket=bucket_name_redirected, ACL="public-read")

        bucket_website_url = _website_bucket_url(bucket_name)
        bucket_website_host = urlparse(bucket_website_url).netloc

        aws_client.s3.put_bucket_website(
            Bucket=bucket_name_redirected,
            WebsiteConfiguration={
                "RedirectAllRequestsTo": {"HostName": bucket_website_host},
            },
        )

        s3_create_bucket(Bucket=bucket_name)
        aws_client.s3.delete_bucket_ownership_controls(Bucket=bucket_name)
        aws_client.s3.delete_public_access_block(Bucket=bucket_name)
        aws_client.s3.put_bucket_acl(Bucket=bucket_name, ACL="public-read")

        aws_client.s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
            },
        )

        aws_client.s3.put_object(
            Bucket=bucket_name,
            Key="index.html",
            Body="index",
            ContentType="text/html",
            ACL="public-read",
        )

        redirected_bucket_website = _website_bucket_url(bucket_name_redirected)

        response_no_redirect = requests.get(redirected_bucket_website, allow_redirects=False)
        assert response_no_redirect.status_code == 301
        assert response_no_redirect.content == b""

        response_redirected = requests.get(redirected_bucket_website)
        assert response_redirected.status_code == 200
        assert response_redirected.content == b"index"

        response = requests.get(bucket_website_url)
        assert response.status_code == 200
        assert response.content == b"index"

        assert response.content == response_redirected.content

        response_redirected = requests.get(f"{redirected_bucket_website}/random-key")
        assert response_redirected.status_code == 404