def test_list_queues_pagination(self, sqs_create_queue, aws_client, snapshot):
        queue_list_length = 10
        # ensures test is unique and prevents conflict in case of parrallel test runs
        test_output_identifier = short_uid_from_seed(SQS_UUID_STRING_SEED)
        max_result_1 = 2
        max_result_2 = 10

        queue_names = [f"{test_output_identifier}-test-queue-{i}" for i in range(queue_list_length)]

        queue_urls = []
        for name in queue_names:
            sqs_create_queue(QueueName=name)
            queue_url = aws_client.sqs.get_queue_url(QueueName=name)["QueueUrl"]
            assert queue_url.endswith(name)
            queue_urls.append(queue_url)

        list_all = aws_client.sqs.list_queues(QueueNamePrefix=test_output_identifier)
        assert "QueueUrls" in list_all
        assert len(list_all["QueueUrls"]) == queue_list_length
        snapshot.match("list_all", list_all)

        list_two_max = aws_client.sqs.list_queues(
            MaxResults=max_result_1, QueueNamePrefix=test_output_identifier
        )
        assert "QueueUrls" in list_two_max
        assert "NextToken" in list_two_max
        assert len(list_two_max["QueueUrls"]) == max_result_1
        snapshot.match("list_two_max", list_two_max)
        next_token = list_two_max["NextToken"]

        list_remaining = aws_client.sqs.list_queues(
            MaxResults=max_result_2, NextToken=next_token, QueueNamePrefix=test_output_identifier
        )
        assert "QueueUrls" in list_remaining
        assert "NextToken" not in list_remaining
        assert len(list_remaining["QueueUrls"]) == max_result_2 - max_result_1
        snapshot.match("list_remaining", list_remaining)

        snapshot.add_transformer(
            snapshot.transform.regex(
                r"https://sqs\.(.+?)\.amazonaws\.com",
                r"http://sqs.\1.localhost.localstack.cloud:4566",
            )
        )

        url = f"http://sqs.<region>.localhost.localstack.cloud:4566/111111111111/{test_output_identifier}-test-queue-{max_result_1 - 1}"
        snapshot.add_transformer(
            snapshot.transform.regex(
                r'("NextToken":\s*")[^"]*(")',
                r"\1" + token_generator(url) + r"\2",
            )
        )