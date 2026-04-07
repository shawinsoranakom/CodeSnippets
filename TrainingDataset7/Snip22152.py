def test_loading_and_dumping(self):
        apps.clear_cache()
        Site.objects.all().delete()
        # Load fixture 1. Single JSON file, with two objects.
        management.call_command("loaddata", "fixture1.json", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            ["Time to reform copyright", "Poker has no place on ESPN"],
        )

        # Dump the current contents of the database as a JSON fixture
        self._dumpdata_assert(
            ["fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Try just dumping the contents of fixtures.Category
        self._dumpdata_assert(
            ["fixtures.Category"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}]',
        )

        # ...and just fixtures.Article
        self._dumpdata_assert(
            ["fixtures.Article"],
            '[{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # ...and both
        self._dumpdata_assert(
            ["fixtures.Category", "fixtures.Article"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Specify a specific model twice
        self._dumpdata_assert(
            ["fixtures.Article", "fixtures.Article"],
            (
                '[{"pk": 2, "model": "fixtures.article", "fields": '
                '{"headline": "Poker has no place on ESPN", '
                '"pub_date": "2006-06-16T12:00:00"}}, '
                '{"pk": 3, "model": "fixtures.article", "fields": '
                '{"headline": "Time to reform copyright", '
                '"pub_date": "2006-06-16T13:00:00"}}]'
            ),
        )

        # Specify a dump that specifies Article both explicitly and implicitly
        self._dumpdata_assert(
            ["fixtures.Article", "fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Specify a dump that specifies Article both explicitly and implicitly,
        # but lists the app first (#22025).
        self._dumpdata_assert(
            ["fixtures", "fixtures.Article"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Same again, but specify in the reverse order
        self._dumpdata_assert(
            ["fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker has no place on ESPN", '
            '"pub_date": "2006-06-16T12:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Time to reform copyright", '
            '"pub_date": "2006-06-16T13:00:00"}}]',
        )

        # Specify one model from one application, and an entire other
        # application.
        self._dumpdata_assert(
            ["fixtures.Category", "sites"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 1, "model": "sites.site", "fields": '
            '{"domain": "example.com", "name": "example.com"}}]',
        )

        # Load fixture 2. JSON file imported by default. Overwrites some
        # existing objects.
        management.call_command("loaddata", "fixture2.json", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker has no place on ESPN",
            ],
        )

        # Load fixture 3, XML format.
        management.call_command("loaddata", "fixture3.xml", verbosity=0)
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "XML identified as leading cause of cancer",
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker on TV is great!",
            ],
        )

        # Load fixture 6, JSON file with dynamic ContentType fields. Testing
        # ManyToOne.
        management.call_command("loaddata", "fixture6.json", verbosity=0)
        self.assertQuerySetEqual(
            Tag.objects.all(),
            [
                '<Tag: <Article: Copyright is fine the way it is> tagged "copyright">',
                '<Tag: <Article: Copyright is fine the way it is> tagged "law">',
            ],
            transform=repr,
            ordered=False,
        )

        # Load fixture 7, XML file with dynamic ContentType fields. Testing
        # ManyToOne.
        management.call_command("loaddata", "fixture7.xml", verbosity=0)
        self.assertQuerySetEqual(
            Tag.objects.all(),
            [
                '<Tag: <Article: Copyright is fine the way it is> tagged "copyright">',
                '<Tag: <Article: Copyright is fine the way it is> tagged "legal">',
                '<Tag: <Article: Django conquers world!> tagged "django">',
                '<Tag: <Article: Django conquers world!> tagged "world domination">',
            ],
            transform=repr,
            ordered=False,
        )

        # Load fixture 8, JSON file with dynamic Permission fields. Testing
        # ManyToMany.
        management.call_command("loaddata", "fixture8.json", verbosity=0)
        self.assertQuerySetEqual(
            Visa.objects.all(),
            [
                "<Visa: Django Reinhardt Can add user, Can change user, Can delete "
                "user>",
                "<Visa: Stephane Grappelli Can add user>",
                "<Visa: Prince >",
            ],
            transform=repr,
            ordered=False,
        )

        # Load fixture 9, XML file with dynamic Permission fields. Testing
        # ManyToMany.
        management.call_command("loaddata", "fixture9.xml", verbosity=0)
        self.assertQuerySetEqual(
            Visa.objects.all(),
            [
                "<Visa: Django Reinhardt Can add user, Can change user, Can delete "
                "user>",
                "<Visa: Stephane Grappelli Can add user, Can delete user>",
                '<Visa: Artist formerly known as "Prince" Can change user>',
            ],
            transform=repr,
            ordered=False,
        )

        # object list is unaffected
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "XML identified as leading cause of cancer",
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker on TV is great!",
            ],
        )

        # By default, you get raw keys on dumpdata
        self._dumpdata_assert(
            ["fixtures.book"],
            '[{"pk": 1, "model": "fixtures.book", "fields": '
            '{"name": "Music for all ages", "authors": [3, 1]}}]',
        )

        # But you can get natural keys if you ask for them and they are
        # available
        self._dumpdata_assert(
            ["fixtures.book"],
            '[{"pk": 1, "model": "fixtures.book", "fields": '
            '{"name": "Music for all ages", "authors": '
            '[["Artist formerly known as \\"Prince\\""], ["Django Reinhardt"]]}}]',
            natural_foreign_keys=True,
        )

        # You can also omit the primary keys for models that we can get later
        # with natural keys.
        self._dumpdata_assert(
            ["fixtures.person"],
            '[{"fields": {"name": "Django Reinhardt"}, "model": "fixtures.person"}, '
            '{"fields": {"name": "Stephane Grappelli"}, "model": "fixtures.person"}, '
            '{"fields": {"name": "Artist formerly known as \\"Prince\\""}, '
            '"model": "fixtures.person"}]',
            natural_primary_keys=True,
        )

        # Dump the current contents of the database as a JSON fixture
        self._dumpdata_assert(
            ["fixtures"],
            '[{"pk": 1, "model": "fixtures.category", "fields": '
            '{"description": "Latest news stories", "title": "News Stories"}}, '
            '{"pk": 2, "model": "fixtures.article", "fields": '
            '{"headline": "Poker on TV is great!", '
            '"pub_date": "2006-06-16T11:00:00"}}, '
            '{"pk": 3, "model": "fixtures.article", "fields": '
            '{"headline": "Copyright is fine the way it is", '
            '"pub_date": "2006-06-16T14:00:00"}}, '
            '{"pk": 4, "model": "fixtures.article", "fields": '
            '{"headline": "Django conquers world!", '
            '"pub_date": "2006-06-16T15:00:00"}}, '
            '{"pk": 5, "model": "fixtures.article", "fields": '
            '{"headline": "XML identified as leading cause of cancer", '
            '"pub_date": "2006-06-16T16:00:00"}}, '
            '{"pk": 1, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "copyright", '
            '"tagged_id": 3}}, '
            '{"pk": 2, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "legal", '
            '"tagged_id": 3}}, '
            '{"pk": 3, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "django", '
            '"tagged_id": 4}}, '
            '{"pk": 4, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "world domination", '
            '"tagged_id": 4}}, '
            '{"pk": 1, "model": "fixtures.person", '
            '"fields": {"name": "Django Reinhardt"}}, '
            '{"pk": 2, "model": "fixtures.person", '
            '"fields": {"name": "Stephane Grappelli"}}, '
            '{"pk": 3, "model": "fixtures.person", '
            '"fields": {"name": "Artist formerly known as \\"Prince\\""}}, '
            '{"pk": 1, "model": "fixtures.visa", '
            '"fields": {"person": ["Django Reinhardt"], "permissions": '
            '[["add_user", "auth", "user"], ["change_user", "auth", "user"], '
            '["delete_user", "auth", "user"]]}}, '
            '{"pk": 2, "model": "fixtures.visa", "fields": '
            '{"person": ["Stephane Grappelli"], "permissions": '
            '[["add_user", "auth", "user"], ["delete_user", "auth", "user"]]}}, '
            '{"pk": 3, "model": "fixtures.visa", "fields": '
            '{"person": ["Artist formerly known as \\"Prince\\""], "permissions": '
            '[["change_user", "auth", "user"]]}}, '
            '{"pk": 1, "model": "fixtures.book", "fields": '
            '{"name": "Music for all ages", "authors": '
            '[["Artist formerly known as \\"Prince\\""], ["Django Reinhardt"]]}}]',
            natural_foreign_keys=True,
        )

        # Dump the current contents of the database as an XML fixture
        self._dumpdata_assert(
            ["fixtures"],
            '<?xml version="1.0" encoding="utf-8"?><django-objects version="1.0">'
            '<object pk="1" model="fixtures.category">'
            '<field type="CharField" name="title">News Stories</field>'
            '<field type="TextField" name="description">Latest news stories</field>'
            "</object>"
            '<object pk="2" model="fixtures.article">'
            '<field type="CharField" name="headline">Poker on TV is great!</field>'
            '<field type="DateTimeField" name="pub_date">2006-06-16T11:00:00</field>'
            "</object>"
            '<object pk="3" model="fixtures.article">'
            '<field type="CharField" name="headline">Copyright is fine the way it is'
            "</field>"
            '<field type="DateTimeField" name="pub_date">2006-06-16T14:00:00</field>'
            "</object>"
            '<object pk="4" model="fixtures.article">'
            '<field type="CharField" name="headline">Django conquers world!</field>'
            '<field type="DateTimeField" name="pub_date">2006-06-16T15:00:00</field>'
            "</object>"
            '<object pk="5" model="fixtures.article">'
            '<field type="CharField" name="headline">'
            "XML identified as leading cause of cancer</field>"
            '<field type="DateTimeField" name="pub_date">2006-06-16T16:00:00</field>'
            "</object>"
            '<object pk="1" model="fixtures.tag">'
            '<field type="CharField" name="name">copyright</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural><natural>article</natural>'
            "</field>"
            '<field type="PositiveIntegerField" name="tagged_id">3</field>'
            "</object>"
            '<object pk="2" model="fixtures.tag">'
            '<field type="CharField" name="name">legal</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural><natural>article</natural>'
            "</field>"
            '<field type="PositiveIntegerField" name="tagged_id">3</field></object>'
            '<object pk="3" model="fixtures.tag">'
            '<field type="CharField" name="name">django</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural><natural>article</natural>'
            "</field>"
            '<field type="PositiveIntegerField" name="tagged_id">4</field>'
            "</object>"
            '<object pk="4" model="fixtures.tag">'
            '<field type="CharField" name="name">world domination</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural><natural>article</natural>'
            "</field>"
            '<field type="PositiveIntegerField" name="tagged_id">4</field>'
            "</object>"
            '<object pk="1" model="fixtures.person">'
            '<field type="CharField" name="name">Django Reinhardt</field>'
            "</object>"
            '<object pk="2" model="fixtures.person">'
            '<field type="CharField" name="name">Stephane Grappelli</field>'
            "</object>"
            '<object pk="3" model="fixtures.person">'
            '<field type="CharField" name="name">Artist formerly known as "Prince"'
            "</field>"
            "</object>"
            '<object pk="1" model="fixtures.visa">'
            '<field to="fixtures.person" name="person" rel="ManyToOneRel">'
            "<natural>Django Reinhardt</natural></field>"
            '<field to="auth.permission" name="permissions" rel="ManyToManyRel">'
            "<object><natural>add_user</natural><natural>auth</natural>"
            "<natural>user</natural></object><object><natural>change_user</natural>"
            "<natural>auth</natural><natural>user</natural></object>"
            "<object><natural>delete_user</natural><natural>auth</natural>"
            "<natural>user</natural></object></field>"
            "</object>"
            '<object pk="2" model="fixtures.visa">'
            '<field to="fixtures.person" name="person" rel="ManyToOneRel">'
            "<natural>Stephane Grappelli</natural></field>"
            '<field to="auth.permission" name="permissions" rel="ManyToManyRel">'
            "<object><natural>add_user</natural><natural>auth</natural>"
            "<natural>user</natural></object>"
            "<object><natural>delete_user</natural><natural>auth</natural>"
            "<natural>user</natural></object></field>"
            "</object>"
            '<object pk="3" model="fixtures.visa">'
            '<field to="fixtures.person" name="person" rel="ManyToOneRel">'
            '<natural>Artist formerly known as "Prince"</natural></field>'
            '<field to="auth.permission" name="permissions" rel="ManyToManyRel">'
            "<object><natural>change_user</natural><natural>auth</natural>"
            "<natural>user</natural></object></field>"
            "</object>"
            '<object pk="1" model="fixtures.book">'
            '<field type="CharField" name="name">Music for all ages</field>'
            '<field to="fixtures.person" name="authors" rel="ManyToManyRel">'
            '<object><natural>Artist formerly known as "Prince"</natural></object>'
            "<object><natural>Django Reinhardt</natural></object></field>"
            "</object></django-objects>",
            format="xml",
            natural_foreign_keys=True,
        )