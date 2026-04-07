def item_title(self, item):
        # Titles should be double escaped by default (see #6533)
        return escape(str(item))