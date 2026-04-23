def test_multi_region_api_gateway(self, aws_client_factory, account_id):
        gw_1 = aws_client_factory(region_name=REGION1).apigateway
        gw_2 = aws_client_factory(region_name=REGION2).apigateway
        gw_3 = aws_client_factory(region_name=REGION3).apigateway
        sqs_1 = aws_client_factory(region_name=REGION3).sqs

        len_1 = len(gw_1.get_rest_apis()["items"])
        len_2 = len(gw_2.get_rest_apis()["items"])

        api_name1 = f"a-{short_uid()}"
        gw_1.create_rest_api(name=api_name1)
        result1 = gw_1.get_rest_apis()["items"]
        assert len(result1) == len_1 + 1
        assert len(gw_2.get_rest_apis()["items"]) == len_2

        api_name2 = f"a-{short_uid()}"
        gw_2.create_rest_api(name=api_name2)
        result2 = gw_2.get_rest_apis()["items"]
        assert len(gw_1.get_rest_apis()["items"]) == len_1 + 1
        assert len(result2) == len_2 + 1

        api_name3 = f"a-{short_uid()}"
        queue_name1 = f"q-{short_uid()}"
        sqs_1.create_queue(QueueName=queue_name1)
        queue_arn = arns.sqs_queue_arn(queue_name1, region_name=REGION3, account_id=account_id)

        result = connect_api_gateway_to_sqs(
            api_name3,
            stage_name="test",
            queue_arn=queue_arn,
            path="/data",
            account_id=account_id,
            region_name=REGION3,
        )

        api_id = result["id"]
        result = gw_3.get_rest_apis()["items"]
        assert result[-1]["name"] == api_name3

        # post message and receive from SQS
        url = self._gateway_request_url(api_id=api_id, stage_name="test", path="/data")
        test_data = {"foo": "bar"}
        result = requests.post(url, data=json.dumps(test_data))
        assert result.status_code == 200
        messages = queries.sqs_receive_message(queue_arn)["Messages"]
        assert len(messages) == 1
        assert json.loads(to_str(base64.b64decode(to_str(messages[0]["Body"])))) == test_data