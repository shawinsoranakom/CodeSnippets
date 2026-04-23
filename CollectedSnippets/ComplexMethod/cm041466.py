def test_notifications_with_filter(
        self,
        s3_bucket,
        s3_create_sqs_bucket_notification,
        sqs_create_queue,
        snapshot,
        aws_client,
    ):
        # create test bucket and queue
        queue_name = f"queue-{short_uid()}"
        queue_url = sqs_create_queue(QueueName=queue_name)

        snapshot.add_transformer(snapshot.transform.regex(queue_name, "<queue>"))
        snapshot.add_transformer(snapshot.transform.regex(s3_bucket, "<bucket>"))
        snapshot.add_transformer(snapshot.transform.s3_notifications_transformer())
        queue_arn = set_policy_for_queue(aws_client.sqs, queue_url, s3_bucket)

        events = ["s3:ObjectCreated:*", "s3:ObjectRemoved:Delete"]
        filter_rules = {
            "FilterRules": [
                {"Name": "Prefix", "Value": "testupload/"},
                {"Name": "Suffix", "Value": "testfile.txt"},
            ]
        }
        aws_client.s3.put_bucket_notification_configuration(
            Bucket=s3_bucket,
            NotificationConfiguration={
                "QueueConfigurations": [
                    {
                        "Id": "id0001",
                        "QueueArn": queue_arn,
                        "Events": events,
                        "Filter": {"Key": filter_rules},
                    },
                    {
                        # Add second config to test fix https://github.com/localstack/localstack/issues/450
                        "Id": "id0002",
                        "QueueArn": queue_arn,
                        "Events": ["s3:ObjectTagging:*"],
                        "Filter": {"Key": filter_rules},
                    },
                ]
            },
        )

        # retrieve and check notification config
        config = aws_client.s3.get_bucket_notification_configuration(Bucket=s3_bucket)
        snapshot.match("config", config)
        assert 2 == len(config["QueueConfigurations"])
        config = [c for c in config["QueueConfigurations"] if c.get("Events")][0]
        assert events == config["Events"]
        assert filter_rules == config["Filter"]["Key"]

        # upload file to S3 (this should NOT trigger a notification)
        test_key1 = "/testdata"
        test_data1 = b'{"test": "bucket_notification1"}'
        aws_client.s3.upload_fileobj(BytesIO(test_data1), s3_bucket, test_key1)

        # upload file to S3 (this should trigger a notification)
        test_key2 = "testupload/dir1/testfile.txt"
        test_data2 = b'{"test": "bucket_notification2"}'
        aws_client.s3.upload_fileobj(BytesIO(test_data2), s3_bucket, test_key2)

        # receive, assert, and delete message from SQS
        messages = sqs_collect_s3_events(aws_client.sqs, queue_url, 1)
        assert len(messages) == 1
        snapshot.match("message", messages[0])
        assert messages[0]["s3"]["object"]["key"] == test_key2
        assert messages[0]["s3"]["bucket"]["name"] == s3_bucket

        # delete notification config
        aws_client.s3.put_bucket_notification_configuration(
            Bucket=s3_bucket, NotificationConfiguration={}
        )
        config = aws_client.s3.get_bucket_notification_configuration(Bucket=s3_bucket)
        snapshot.match("config_empty", config)
        assert not config.get("QueueConfigurations")
        assert not config.get("TopicConfiguration")
        # put notification config with single event type
        event = "s3:ObjectCreated:*"
        aws_client.s3.put_bucket_notification_configuration(
            Bucket=s3_bucket,
            NotificationConfiguration={
                "QueueConfigurations": [
                    {"Id": "id123456", "QueueArn": queue_arn, "Events": [event]}
                ]
            },
        )
        config = aws_client.s3.get_bucket_notification_configuration(Bucket=s3_bucket)
        snapshot.match("config_updated", config)
        config = config["QueueConfigurations"][0]
        assert [event] == config["Events"]

        # put notification config with single event type
        event = "s3:ObjectCreated:*"
        filter_rules = {"FilterRules": [{"Name": "Prefix", "Value": "testupload/"}]}
        aws_client.s3.put_bucket_notification_configuration(
            Bucket=s3_bucket,
            NotificationConfiguration={
                "QueueConfigurations": [
                    {
                        "Id": "id123456",
                        "QueueArn": queue_arn,
                        "Events": [event],
                        "Filter": {"Key": filter_rules},
                    }
                ]
            },
        )
        config = aws_client.s3.get_bucket_notification_configuration(Bucket=s3_bucket)
        snapshot.match("config_updated_filter", config)
        config = config["QueueConfigurations"][0]
        assert [event] == config["Events"]
        assert filter_rules == config["Filter"]["Key"]