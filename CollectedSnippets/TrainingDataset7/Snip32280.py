def get_languages_for_item(self, item):
        if item.name == "Only for PT":
            return ["pt"]
        return super().get_languages_for_item(item)