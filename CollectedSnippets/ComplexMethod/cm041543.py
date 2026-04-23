def test_delete_queue_multi_account(
        self,
        aws_sqs_client,
        secondary_aws_client,
        aws_http_client_factory,
        cleanups,
        account_id,
        secondary_account_id,
        region_name,
    ):
        # set up regular boto clients for creating the queues
        client1 = aws_sqs_client
        client2 = secondary_aws_client.sqs

        # set up the queues in the two accounts
        prefix = f"test-{short_uid()}-"
        queue1_name = f"{prefix}-queue-{short_uid()}"
        queue2_name = f"{prefix}-queue-{short_uid()}"
        response = client1.create_queue(QueueName=queue1_name)
        queue1_url = response["QueueUrl"]
        assert parse_queue_url(queue1_url)[0] == account_id

        response = client2.create_queue(QueueName=queue2_name)
        queue2_url = response["QueueUrl"]
        assert parse_queue_url(queue2_url)[0] == secondary_account_id

        # now prepare the query api clients
        client1_http = aws_http_client_factory(
            service="sqs",
            region=region_name,
            aws_access_key_id=TEST_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=TEST_AWS_SECRET_ACCESS_KEY,
        )

        client2_http = aws_http_client_factory(
            service="sqs",
            region=region_name,  # Use the same region for both clients
            aws_access_key_id=SECONDARY_TEST_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=SECONDARY_TEST_AWS_SECRET_ACCESS_KEY,
        )

        # try and delete the queue from one account using the query API and make sure a) it works, and b) it's not deleting the queue from the other account
        assert len(client1.list_queues(QueueNamePrefix=prefix).get("QueueUrls", [])) == 1
        assert len(client2.list_queues(QueueNamePrefix=prefix).get("QueueUrls", [])) == 1
        response = client1_http.post(queue1_url, params={"Action": "DeleteQueue"})
        assert response.ok
        assert len(client1.list_queues(QueueNamePrefix=prefix).get("QueueUrls", [])) == 0
        assert queue2_url in client2.list_queues(QueueNamePrefix=prefix).get("QueueUrls", [])

        # now delete the second one
        client2_http.post(queue2_url, params={"Action": "DeleteQueue"})
        assert response.ok
        assert len(client2.list_queues(QueueNamePrefix=prefix).get("QueueUrls", [])) == 0