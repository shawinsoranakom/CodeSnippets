def test_get_send_and_receive_messages(self, sqs_create_queue, sqs_http_client):
        queue1_url = sqs_create_queue()
        queue2_url = sqs_create_queue()

        # items in queue 1
        response = sqs_http_client.get(
            queue1_url,
            params={
                "Action": "SendMessage",
                "MessageBody": "foobar",
            },
        )
        assert response.ok

        # no items in queue 2
        response = sqs_http_client.get(
            queue2_url,
            params={
                "Action": "ReceiveMessage",
            },
        )
        assert response.ok
        assert "foobar" not in response.text
        assert "<ReceiveMessageResult/>" in response.text.replace(
            " />", "/>"
        )  # expect response to be empty

        # get items from queue 1
        response = sqs_http_client.get(
            queue1_url,
            params={
                "Action": "ReceiveMessage",
            },
        )

        assert response.ok
        assert "<Body>foobar</Body>" in response.text
        assert "<MD5OfBody>" in response.text