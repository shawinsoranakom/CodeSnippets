def test_atom_add_item(self):
        # Not providing any optional arguments to Atom1Feed.add_item()
        feed = feedgenerator.Atom1Feed("title", "/link/", "descr")
        feed.add_item("item_title", "item_link", "item_description")
        feed.writeString("utf-8")