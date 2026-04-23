def test_list_keys(self, kms_create_key, aws_client):
        created_key = kms_create_key()
        next_token = None
        while True:
            kwargs = {"nextToken": next_token} if next_token else {}
            response = aws_client.kms.list_keys(**kwargs)
            for key in response["Keys"]:
                assert key["KeyId"]
                assert key["KeyArn"]
                if key["KeyId"] == created_key["KeyId"]:
                    assert key["KeyArn"] == created_key["Arn"]
            if "nextToken" not in response:
                break
            next_token = response["nextToken"]