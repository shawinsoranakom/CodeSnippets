def remove_tags(self, items):
        # items: REMOVE, TAGS, quoted_string(tag1), quoted_string(tag2), ..., FROM, DATASET, quoted_string(dataset_name), ";"
        tags = []
        # Start from index 2 (after TAGS keyword) and parse quoted strings until FROM
        for i in range(2, len(items)):
            item = items[i]
            # Check for FROM token to stop
            if hasattr(item, 'type') and item.type == 'FROM':
                break
            if hasattr(item, 'children') and item.children:
                tag = item.children[0].strip("'\"")
                tags.append(tag)
        # Find dataset_name: quoted_string after DATASET
        dataset_name = None
        for i, item in enumerate(items):
            # Check if item is a DATASET token
            if hasattr(item, 'type') and item.type == 'DATASET':
                # Next item should be quoted_string
                dataset_name = items[i + 1].children[0].strip("'\"")
                break
        return {"type": "remove_tags", "dataset_name": dataset_name, "tags": tags}