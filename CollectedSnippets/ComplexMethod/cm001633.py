def dumpjson(self):
        d = {k: self.data.get(k, v.default) for k, v in self.data_labels.items()}
        d["_comments_before"] = {k: v.comment_before for k, v in self.data_labels.items() if v.comment_before is not None}
        d["_comments_after"] = {k: v.comment_after for k, v in self.data_labels.items() if v.comment_after is not None}

        item_categories = {}
        for item in self.data_labels.values():
            if item.section[0] is None:
                continue

            category = categories.mapping.get(item.category_id)
            category = "Uncategorized" if category is None else category.label
            if category not in item_categories:
                item_categories[category] = item.section[1]

        # _categories is a list of pairs: [section, category]. Each section (a setting page) will get a special heading above it with the category as text.
        d["_categories"] = [[v, k] for k, v in item_categories.items()] + [["Defaults", "Other"]]

        return json.dumps(d)