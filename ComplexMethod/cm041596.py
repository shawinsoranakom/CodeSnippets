def test_reusable_delegation_sets(self, aws_client):
        client = aws_client.route53

        sets_before = client.list_reusable_delegation_sets().get("DelegationSets", [])

        call_ref_1 = f"c-{short_uid()}"
        result_1 = client.create_reusable_delegation_set(CallerReference=call_ref_1)[
            "DelegationSet"
        ]
        set_id_1 = result_1["Id"]

        call_ref_2 = f"c-{short_uid()}"
        result_2 = client.create_reusable_delegation_set(CallerReference=call_ref_2)[
            "DelegationSet"
        ]
        set_id_2 = result_2["Id"]

        result_1 = client.get_reusable_delegation_set(Id=set_id_1)
        assert result_1["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert result_1["DelegationSet"]["Id"] == set_id_1

        result_1 = client.list_reusable_delegation_sets()
        assert result_1["ResponseMetadata"]["HTTPStatusCode"] == 200
        # TODO: assertion should be updated, to allow for parallel tests
        assert len(result_1["DelegationSets"]) == len(sets_before) + 2

        result_1 = client.delete_reusable_delegation_set(Id=set_id_1)
        assert result_1["ResponseMetadata"]["HTTPStatusCode"] == 200

        result_2 = client.delete_reusable_delegation_set(Id=set_id_2)
        assert result_2["ResponseMetadata"]["HTTPStatusCode"] == 200

        with pytest.raises(Exception) as ctx:
            client.get_reusable_delegation_set(Id=set_id_1)
        assert "NoSuchDelegationSet" in str(ctx.value)