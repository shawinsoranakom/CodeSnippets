def update_tags(self, ssm, model, new_tags):
        current_tags = ssm.list_tags_for_resource(
            ResourceType="Parameter", ResourceId=model["Name"]
        )["TagList"]
        current_tags = {tag["Key"]: tag["Value"] for tag in current_tags}

        new_tag_keys = set(new_tags.keys())
        old_tag_keys = set(current_tags.keys())
        potentially_modified_tag_keys = new_tag_keys.intersection(old_tag_keys)
        tag_keys_to_add = new_tag_keys.difference(old_tag_keys)
        tag_keys_to_remove = old_tag_keys.difference(new_tag_keys)

        for tag_key in potentially_modified_tag_keys:
            if new_tags[tag_key] != current_tags[tag_key]:
                tag_keys_to_add.add(tag_key)

        if tag_keys_to_add:
            ssm.add_tags_to_resource(
                ResourceType="Parameter",
                ResourceId=model["Name"],
                Tags=[
                    {"Key": tag_key, "Value": tag_value}
                    for tag_key, tag_value in new_tags.items()
                    if tag_key in tag_keys_to_add
                ],
            )

        if tag_keys_to_remove:
            ssm.remove_tags_from_resource(
                ResourceType="Parameter", ResourceId=model["Name"], TagKeys=tag_keys_to_remove
            )