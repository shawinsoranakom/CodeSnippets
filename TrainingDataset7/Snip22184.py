def test_output_formats(self):
        # Load back in fixture 1, we need the articles from it
        management.call_command("loaddata", "fixture1", verbosity=0)

        # Try to load fixture 6 using format discovery
        management.call_command("loaddata", "fixture6", verbosity=0)
        self.assertQuerySetEqual(
            Tag.objects.all(),
            [
                '<Tag: <Article: Time to reform copyright> tagged "copyright">',
                '<Tag: <Article: Time to reform copyright> tagged "law">',
            ],
            transform=repr,
            ordered=False,
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
            '"pub_date": "2006-06-16T13:00:00"}}, '
            '{"pk": 1, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "copyright", '
            '"tagged_id": 3}}, '
            '{"pk": 2, "model": "fixtures.tag", "fields": '
            '{"tagged_type": ["fixtures", "article"], "name": "law", "tagged_id": 3}}, '
            '{"pk": 1, "model": "fixtures.person", "fields": '
            '{"name": "Django Reinhardt"}}, '
            '{"pk": 2, "model": "fixtures.person", "fields": '
            '{"name": "Stephane Grappelli"}}, '
            '{"pk": 3, "model": "fixtures.person", "fields": {"name": "Prince"}}]',
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
            '<field type="CharField" name="headline">Poker has no place on ESPN</field>'
            '<field type="DateTimeField" name="pub_date">2006-06-16T12:00:00</field>'
            "</object>"
            '<object pk="3" model="fixtures.article">'
            '<field type="CharField" name="headline">Time to reform copyright</field>'
            '<field type="DateTimeField" name="pub_date">2006-06-16T13:00:00</field>'
            "</object>"
            '<object pk="1" model="fixtures.tag">'
            '<field type="CharField" name="name">copyright</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural>'
            "<natural>article</natural></field>"
            '<field type="PositiveIntegerField" name="tagged_id">3</field>'
            "</object>"
            '<object pk="2" model="fixtures.tag">'
            '<field type="CharField" name="name">law</field>'
            '<field to="contenttypes.contenttype" name="tagged_type" '
            'rel="ManyToOneRel"><natural>fixtures</natural>'
            "<natural>article</natural></field>"
            '<field type="PositiveIntegerField" name="tagged_id">3</field>'
            "</object>"
            '<object pk="1" model="fixtures.person">'
            '<field type="CharField" name="name">Django Reinhardt</field>'
            "</object>"
            '<object pk="2" model="fixtures.person">'
            '<field type="CharField" name="name">Stephane Grappelli</field>'
            "</object>"
            '<object pk="3" model="fixtures.person">'
            '<field type="CharField" name="name">Prince</field>'
            "</object></django-objects>",
            format="xml",
            natural_foreign_keys=True,
        )