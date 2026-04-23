def test_list_state_machine_versions_pagination(
        self,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
        aws_client,
        aws_client_no_retry,
    ):
        snf_role_arn = create_state_machine_iam_role(aws_client)
        sfn_snapshot.add_transformer(RegexTransformer(snf_role_arn, "snf_role_arn"))

        definition = BaseTemplate.load_sfn_template(BaseTemplate.BASE_PASS_RESULT)
        definition_str = json.dumps(definition)

        sm_name = f"statemachine_{short_uid()}"
        creation_resp_1 = create_state_machine(
            aws_client, name=sm_name, definition=definition_str, roleArn=snf_role_arn
        )
        sfn_snapshot.add_transformer(sfn_snapshot.transform.sfn_sm_create_arn(creation_resp_1, 0))
        sfn_snapshot.match("creation_resp_1", creation_resp_1)
        state_machine_arn = creation_resp_1["stateMachineArn"]

        state_machine_version_arns = []
        for revision_no in range(1, 14):
            definition["Comment"] = f"{definition['Comment']}-R{revision_no}"
            definition_raw_str = json.dumps(definition)

            update_resp_1 = aws_client.stepfunctions.update_state_machine(
                stateMachineArn=state_machine_arn, definition=definition_raw_str, publish=True
            )

            state_machine_version_arn: str = update_resp_1["stateMachineVersionArn"]
            assert state_machine_version_arn == f"{state_machine_arn}:{revision_no}"

            state_machine_version_arns.append(state_machine_version_arn)

            await_state_machine_version_listed(
                aws_client.stepfunctions,
                state_machine_arn,
                update_resp_1["stateMachineVersionArn"],
            )

        page_1_state_machine_versions = aws_client.stepfunctions.list_state_machine_versions(
            stateMachineArn=state_machine_arn,
            maxResults=10,
        )
        sfn_snapshot.add_transformer(sfn_snapshot.transform.key_value("nextToken"))
        sfn_snapshot.match("list-state-machine-versions-page-1", page_1_state_machine_versions)

        page_2_state_machine_versions = aws_client.stepfunctions.list_state_machine_versions(
            stateMachineArn=state_machine_arn,
            maxResults=3,
            nextToken=page_1_state_machine_versions["nextToken"],
        )
        sfn_snapshot.match("list-state-machine-versions-page-2", page_2_state_machine_versions)

        assert all(
            sm not in page_1_state_machine_versions["stateMachineVersions"]
            for sm in page_2_state_machine_versions["stateMachineVersions"]
        )

        # maxResults value is out of bounds
        with pytest.raises(Exception) as err:
            aws_client_no_retry.stepfunctions.list_state_machine_versions(
                stateMachineArn=state_machine_arn, maxResults=1001
            )
        sfn_snapshot.match(
            "list-state-machine-versions-invalid-param-too-large", err.value.response
        )

        # nextToken is too short
        with pytest.raises(Exception) as err:
            aws_client_no_retry.stepfunctions.list_state_machine_versions(
                stateMachineArn=state_machine_arn, nextToken=""
            )
        sfn_snapshot.match(
            "list-state-machine-versions-param-short-nextToken",
            {"exception_typename": err.typename, "exception_value": err.value},
        )

        # nextToken is too long
        invalid_long_token = "x" * 1025
        with pytest.raises(Exception) as err:
            aws_client_no_retry.stepfunctions.list_state_machine_versions(
                stateMachineArn=state_machine_arn, nextToken=invalid_long_token
            )
        sfn_snapshot.add_transformer(
            RegexTransformer(invalid_long_token, f"<invalid_token_{len(invalid_long_token)}_chars>")
        )
        sfn_snapshot.match(
            "list-state-machine-versions-invalid-param-long-nextToken", err.value.response
        )

        # where maxResults is 0, the default of 100 should be returned
        state_machines_default_all_returned = aws_client.stepfunctions.list_state_machine_versions(
            stateMachineArn=state_machine_arn, maxResults=0
        )
        assert len(state_machines_default_all_returned["stateMachineVersions"]) == 13
        assert "nextToken" not in state_machines_default_all_returned

        for state_machine_version_arn in state_machine_version_arns:
            aws_client.stepfunctions.delete_state_machine_version(
                stateMachineVersionArn=state_machine_version_arn,
            )

        for state_machine_version_arn in state_machine_version_arns:
            await_state_machine_version_not_listed(
                aws_client.stepfunctions, state_machine_arn, state_machine_version_arn
            )

        ls_with_no_state_machine_versions_present = (
            aws_client.stepfunctions.list_state_machine_versions(
                stateMachineArn=state_machine_arn, maxResults=len(state_machine_version_arns)
            )
        )

        assert len(ls_with_no_state_machine_versions_present["stateMachineVersions"]) == 0