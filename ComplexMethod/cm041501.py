def test_update_secret_version_stages_current_pending_cycle_custom_stages_3(
        self, sm_snapshot, secret_name, aws_client
    ):
        create_secret_rs = aws_client.secretsmanager.create_secret(
            Name=secret_name, SecretString="SS"
        )
        sm_snapshot.add_transformers_list(
            sm_snapshot.transform.secretsmanager_secret_id_arn(create_secret_rs, 0)
        )
        sm_snapshot.match("create_secret_rs", create_secret_rs)

        version_id_v1 = create_secret_rs["VersionId"]

        put_secret_value_rs = aws_client.secretsmanager.put_secret_value(
            SecretId=secret_name, SecretString="S1", VersionStages=["PENDING"]
        )
        sm_snapshot.match("put_secret_value_res_0", put_secret_value_rs)

        version_id_v2 = put_secret_value_rs["VersionId"]

        list_secret_version_ids_rs = aws_client.secretsmanager.list_secret_version_ids(
            SecretId=secret_name
        )
        sm_snapshot.match("list_secret_version_ids_rs", list_secret_version_ids_rs)
        versions = list_secret_version_ids_rs["Versions"]
        assert len(versions) == 2

        get_secret_value_v1_rs = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v1,
        )
        sm_snapshot.match("get_secret_value_v1_rs", get_secret_value_v1_rs)
        assert get_secret_value_v1_rs["VersionStages"] == ["AWSCURRENT"]

        get_secret_value_v2_rs = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v2,
        )
        sm_snapshot.match("get_secret_value_v2_rs", get_secret_value_v2_rs)
        assert get_secret_value_v2_rs["VersionStages"] == ["PENDING"]

        update_secret_version_stage_res_1 = aws_client.secretsmanager.update_secret_version_stage(
            SecretId=secret_name,
            RemoveFromVersionId=version_id_v1,
            MoveToVersionId=version_id_v2,
            VersionStage="AWSCURRENT",
        )
        sm_snapshot.match("update_secret_version_stage_res_1", update_secret_version_stage_res_1)

        get_secret_value_v1_rs_1 = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v1,
        )
        sm_snapshot.match("get_secret_value_v1_rs_1", get_secret_value_v1_rs_1)
        assert get_secret_value_v1_rs_1["VersionStages"] == ["AWSPREVIOUS"]

        get_secret_value_v2_rs_1 = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v2,
        )
        sm_snapshot.match("get_secret_value_v2_rs_1", get_secret_value_v2_rs_1)
        assert sorted(get_secret_value_v2_rs_1["VersionStages"]) == sorted(
            ["AWSCURRENT", "PENDING"]
        )

        update_secret_version_stage_res_2 = aws_client.secretsmanager.update_secret_version_stage(
            SecretId=secret_name,
            RemoveFromVersionId=version_id_v2,
            VersionStage="PENDING",
        )
        sm_snapshot.match("update_secret_version_stage_res_2", update_secret_version_stage_res_2)

        get_secret_value_v1_rs_2 = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v1,
        )
        sm_snapshot.match("get_secret_value_v1_rs_2", get_secret_value_v1_rs_2)
        assert get_secret_value_v1_rs_2["VersionStages"] == ["AWSPREVIOUS"]

        get_secret_value_v2_rs_2 = aws_client.secretsmanager.get_secret_value(
            SecretId=secret_name,
            VersionId=version_id_v2,
        )
        sm_snapshot.match("get_secret_value_v2_rs_2", get_secret_value_v2_rs_2)
        assert get_secret_value_v2_rs_2["VersionStages"] == ["AWSCURRENT"]

        delete_secret_res_0 = aws_client.secretsmanager.delete_secret(
            SecretId=secret_name, ForceDeleteWithoutRecovery=True
        )
        sm_snapshot.match("delete_secret_res_0", delete_secret_res_0)