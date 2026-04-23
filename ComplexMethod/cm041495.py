def test_bucket_lifecycle_configuration_object_expiry_versioned(
        self, s3_bucket, snapshot, aws_client
    ):
        snapshot.add_transformer(snapshot.transform.key_value("VersionId"), priority=-1)
        snapshot.add_transformer(
            [
                snapshot.transform.key_value("BucketName"),
                snapshot.transform.key_value(
                    "Expiration", reference_replacement=False, value_replacement="<expiration>"
                ),
            ]
        )

        aws_client.s3.put_bucket_versioning(
            Bucket=s3_bucket, VersioningConfiguration={"Status": "Enabled"}
        )
        rule_id = "rule2"
        current_exp_days = 3
        non_current_exp_days = 1
        lfc = {
            "Rules": [
                {
                    "ID": rule_id,
                    "Status": "Enabled",
                    "Filter": {},
                    "Expiration": {"Days": current_exp_days},
                    "NoncurrentVersionExpiration": {"NoncurrentDays": non_current_exp_days},
                }
            ]
        }
        aws_client.s3.put_bucket_lifecycle_configuration(
            Bucket=s3_bucket, LifecycleConfiguration=lfc
        )
        result = aws_client.s3.get_bucket_lifecycle_configuration(Bucket=s3_bucket)
        snapshot.match("get-bucket-lifecycle-conf", result)

        key = "test-object-expiry"
        put_object_1 = aws_client.s3.put_object(Body=b"test", Bucket=s3_bucket, Key=key)
        version_id_1 = put_object_1["VersionId"]

        response = aws_client.s3.head_object(Bucket=s3_bucket, Key=key)
        snapshot.match("head-object-expiry", response)

        parsed_exp_date, parsed_exp_rule = parse_expiration_header(response["Expiration"])
        assert parsed_exp_rule == rule_id
        # use a bit of margin for the days expiration, as it can depend on the time of day, but at least we validate
        assert (
            current_exp_days - 1
            <= (parsed_exp_date - response["LastModified"]).days
            <= current_exp_days + 1
        )

        key = "test-object-expiry"
        put_object_2 = aws_client.s3.put_object(Body=b"test", Bucket=s3_bucket, Key=key)
        version_id_2 = put_object_2["VersionId"]

        response = aws_client.s3.head_object(Bucket=s3_bucket, Key=key, VersionId=version_id_1)
        snapshot.match("head-object-expiry-noncurrent", response)

        # This is not in the documentation anymore, but it still seems to be the case
        # See https://stackoverflow.com/questions/33096697/object-expiration-of-non-current-version
        # Note that for versioning-enabled buckets, this header applies only to current versions; Amazon S3 does not
        # provide a header to infer when a noncurrent version will be eligible for permanent deletion.
        assert "Expiration" not in response

        # if you specify the VersionId, AWS won't return the Expiration header, even if that's the current version
        response = aws_client.s3.head_object(Bucket=s3_bucket, Key=key, VersionId=version_id_2)
        snapshot.match("head-object-expiry-current-with-version-id", response)
        assert "Expiration" not in response

        response = aws_client.s3.head_object(Bucket=s3_bucket, Key=key)
        snapshot.match("head-object-expiry-current-without-version-id", response)
        # assert that the previous version id which didn't return the Expiration header is the same object
        assert response["VersionId"] == version_id_2

        parsed_exp_date, parsed_exp_rule = parse_expiration_header(response["Expiration"])
        assert parsed_exp_rule == rule_id
        # use a bit of margin for the days expiration, as it can depend on the time of day, but at least we validate
        assert (
            current_exp_days - 1
            <= (parsed_exp_date - response["LastModified"]).days
            <= current_exp_days + 1
        )