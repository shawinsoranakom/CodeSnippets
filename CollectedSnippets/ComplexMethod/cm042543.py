def test_parse_credentials(self):
        aws_credentials = {
            "AWS_ACCESS_KEY_ID": "settings_key",
            "AWS_SECRET_ACCESS_KEY": "settings_secret",
            "AWS_SESSION_TOKEN": "settings_token",
        }
        crawler = get_crawler(settings_dict=aws_credentials)
        # Instantiate with crawler
        storage = S3FeedStorage.from_crawler(
            crawler,
            "s3://mybucket/export.csv",
        )
        assert storage.access_key == "settings_key"
        assert storage.secret_key == "settings_secret"
        assert storage.session_token == "settings_token"
        # Instantiate directly
        storage = S3FeedStorage(
            "s3://mybucket/export.csv",
            aws_credentials["AWS_ACCESS_KEY_ID"],
            aws_credentials["AWS_SECRET_ACCESS_KEY"],
            session_token=aws_credentials["AWS_SESSION_TOKEN"],
        )
        assert storage.access_key == "settings_key"
        assert storage.secret_key == "settings_secret"
        assert storage.session_token == "settings_token"
        # URI priority > settings priority
        storage = S3FeedStorage(
            "s3://uri_key:uri_secret@mybucket/export.csv",
            aws_credentials["AWS_ACCESS_KEY_ID"],
            aws_credentials["AWS_SECRET_ACCESS_KEY"],
        )
        assert storage.access_key == "uri_key"
        assert storage.secret_key == "uri_secret"