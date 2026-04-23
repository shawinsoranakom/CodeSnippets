def test_list_retirable_grants(self, kms_create_key, kms_create_grant, aws_client):
        retiring_principal_arn_prefix = (
            "arn:aws:kms:eu-central-1:123456789876:key/198a5a78-52c3-489f-ac70-"
        )
        right_retiring_principal = retiring_principal_arn_prefix + "000000000001"
        wrong_retiring_principal = retiring_principal_arn_prefix + "000000000002"
        key_id = kms_create_key()["KeyId"]
        right_grant_id = kms_create_grant(KeyId=key_id, RetiringPrincipal=right_retiring_principal)[
            0
        ]
        wrong_grant_id_one = kms_create_grant(
            KeyId=key_id, RetiringPrincipal=wrong_retiring_principal
        )[0]
        wrong_grant_id_two = kms_create_grant(KeyId=key_id)[0]
        wrong_grant_ids = [wrong_grant_id_one, wrong_grant_id_two]

        next_token = None
        right_grant_found = False
        wrong_grant_found = False
        while True:
            kwargs = {"nextToken": next_token} if next_token else {}
            response = aws_client.kms.list_retirable_grants(
                RetiringPrincipal=right_retiring_principal, **kwargs
            )
            for grant in response["Grants"]:
                if grant["GrantId"] == right_grant_id:
                    right_grant_found = True
                if grant["GrantId"] in wrong_grant_ids:
                    wrong_grant_found = True
            if "nextToken" not in response:
                break
            next_token = response["nextToken"]

        assert right_grant_found
        assert not wrong_grant_found