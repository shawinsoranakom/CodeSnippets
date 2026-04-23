def test_bucket_notifications_with_filter(
        self,
        sqs_create_queue,
        sns_create_topic,
        s3_bucket,
        sns_create_sqs_subscription,
        snapshot,
        aws_client,
    ):
        # Tests s3->sns->sqs notifications
        #
        queue_name = f"queue-{short_uid()}"
        topic_arn = sns_create_topic()["TopicArn"]
        queue_url = sqs_create_queue(QueueName=queue_name)

        snapshot.add_transformer(snapshot.transform.regex(queue_name, "<queue>"))
        snapshot.add_transformer(snapshot.transform.s3_notifications_transformer())
        snapshot.add_transformer(snapshot.transform.sns_api())

        # connect topic to queue
        sns_create_sqs_subscription(topic_arn, queue_url)
        create_sns_bucket_notification(
            aws_client.s3, aws_client.sns, s3_bucket, topic_arn, ["s3:ObjectCreated:*"]
        )
        aws_client.s3.put_bucket_notification_configuration(
            Bucket=s3_bucket,
            NotificationConfiguration={
                "TopicConfigurations": [
                    {
                        "Id": "id123",
                        "Events": ["s3:ObjectCreated:*"],
                        "TopicArn": topic_arn,
                        "Filter": {
                            "Key": {"FilterRules": [{"Name": "Prefix", "Value": "testupload/"}]}
                        },
                    }
                ]
            },
        )
        test_key1 = "test/dir1/myfile.txt"
        test_key2 = "testupload/dir1/testfile.txt"
        test_data = b'{"test": "bucket_notification one"}'

        aws_client.s3.upload_fileobj(BytesIO(test_data), s3_bucket, test_key1)
        aws_client.s3.upload_fileobj(BytesIO(test_data), s3_bucket, test_key2)

        messages = sqs_collect_sns_messages(aws_client.sqs, queue_url, 1)
        assert len(messages) == 1
        snapshot.match("message", messages[0])
        message = messages[0]
        assert message["Type"] == "Notification"
        assert message["TopicArn"] == topic_arn
        assert message["Subject"] == "Amazon S3 Notification"

        event = json.loads(message["Message"])["Records"][0]
        assert event["eventSource"] == "aws:s3"
        assert event["eventName"] == "ObjectCreated:Put"
        assert event["s3"]["bucket"]["name"] == s3_bucket
        assert event["s3"]["object"]["key"] == test_key2