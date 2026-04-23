def test_instance_profile_tags(self, aws_client, cleanups):
        def gen_tag():
            return Tag(Key=f"key-{long_uid()}", Value=f"value-{short_uid()}")

        def _sort_key(entry):
            return entry["Key"]

        user_name = f"user-role-{short_uid()}"
        aws_client.iam.create_instance_profile(InstanceProfileName=user_name)
        cleanups.append(
            lambda: aws_client.iam.delete_instance_profile(InstanceProfileName=user_name)
        )

        tags_v0 = []
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == tags_v0.sort(key=_sort_key)

        tags_v1 = [gen_tag()]
        #
        rs = aws_client.iam.tag_instance_profile(InstanceProfileName=user_name, Tags=tags_v1)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == tags_v1.sort(key=_sort_key)

        tags_v2_new = [gen_tag() for _ in range(5)]
        tags_v2 = tags_v1 + tags_v2_new
        rs = aws_client.iam.tag_instance_profile(InstanceProfileName=user_name, Tags=tags_v2)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == tags_v2.sort(key=_sort_key)

        rs = aws_client.iam.tag_instance_profile(InstanceProfileName=user_name, Tags=tags_v2)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == tags_v2.sort(key=_sort_key)

        tags_v3_new = [gen_tag()]
        tags_v3 = tags_v1 + tags_v3_new
        target_tags_v3 = tags_v2 + tags_v3_new
        rs = aws_client.iam.tag_instance_profile(InstanceProfileName=user_name, Tags=tags_v3)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == target_tags_v3.sort(key=_sort_key)

        tags_v4 = tags_v1
        target_tags_v4 = target_tags_v3
        rs = aws_client.iam.tag_instance_profile(InstanceProfileName=user_name, Tags=tags_v4)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == target_tags_v4.sort(key=_sort_key)

        tags_u_v1 = [tag["Key"] for tag in tags_v1]
        target_tags_u_v1 = tags_v2_new + tags_v3_new
        aws_client.iam.untag_instance_profile(InstanceProfileName=user_name, TagKeys=tags_u_v1)
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == target_tags_u_v1.sort(key=_sort_key)

        tags_u_v2 = [f"key-{long_uid()}"]
        target_tags_u_v2 = target_tags_u_v1
        aws_client.iam.untag_instance_profile(InstanceProfileName=user_name, TagKeys=tags_u_v2)
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == target_tags_u_v2.sort(key=_sort_key)

        tags_u_v3 = [tag["Key"] for tag in target_tags_u_v1]
        target_tags_u_v3 = []
        aws_client.iam.untag_instance_profile(InstanceProfileName=user_name, TagKeys=tags_u_v3)
        #
        rs = aws_client.iam.list_instance_profile_tags(InstanceProfileName=user_name)
        assert rs["Tags"].sort(key=_sort_key) == target_tags_u_v3.sort(key=_sort_key)