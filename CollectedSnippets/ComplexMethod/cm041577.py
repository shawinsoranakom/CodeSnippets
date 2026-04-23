def test_create_group(self, aws_client, resourcegroups_create_group, snapshot):
        name = f"resource_group-{short_uid()}"
        response = resourcegroups_create_group(
            Name=name,
            Description="description",
            ResourceQuery={
                "Type": "TAG_FILTERS_1_0",
                "Query": json.dumps(
                    {
                        "ResourceTypeFilters": ["AWS::AllSupported"],
                        "TagFilters": [
                            {
                                "Key": "resources_tag_key",
                                "Values": ["resources_tag_value"],
                            }
                        ],
                    }
                ),
            },
            Tags={"resource_group_tag_key": "resource_group_tag_value"},
        )
        snapshot.match("create-group", response)
        assert name == response["Group"]["Name"]
        assert "TAG_FILTERS_1_0" == response["ResourceQuery"]["Type"]
        assert "resource_group_tag_value" == response["Tags"]["resource_group_tag_key"]

        response = aws_client.resource_groups.get_group(GroupName=name)
        snapshot.match("get-group", response)
        assert "description" == response["Group"]["Description"]

        response = aws_client.resource_groups.list_groups()
        snapshot.match("list-groups", response)
        assert 1 == len(response["GroupIdentifiers"])
        assert 1 == len(response["Groups"])

        response = aws_client.resource_groups.delete_group(GroupName=name)
        snapshot.match("delete-group", response)
        assert name == response["Group"]["Name"]

        response = aws_client.resource_groups.list_groups()
        snapshot.match("list-groups-after-delete", response)
        assert 0 == len(response["GroupIdentifiers"])
        assert 0 == len(response["Groups"])