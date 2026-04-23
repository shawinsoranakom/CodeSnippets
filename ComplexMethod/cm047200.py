def test_properties_field_read_group_tags(self):
        Model = self.env['test_orm.message']

        (self.message_1 | self.message_2 | self.message_3).discussion = self.discussion_1

        # group by tags property
        self.message_1.attributes = [{
            'name': 'mytags',
            'type': 'tags',
            'value': ['a', 'c', 'g'],
            'tags': [[x.lower(), x, i] for i, x in enumerate('ABCDEFG')],
            'definition_changed': True,
        }]
        self.message_2.attributes = {'mytags': ['a', 'e', 'g']}
        self.env.cr.execute(
            """
            UPDATE test_orm_message
               SET attributes = '{"mytags": ["a", "d", "invalid", "e"]}'
             WHERE id = %s
            """,
            [self.message_3.id],
        )
        self.env.invalidate_all()

        with self.assertQueryCount(3):
            result = Model.formatted_read_group(
                domain=[('discussion', '!=', self.wrong_discussion_id)],
                aggregates=['__count'],
                groupby=['attributes.mytags'],
            )

        self.assertNotIn('invalid', str(result))
        self.assertEqual(len(result), 6)

        all_tags = self.message_1.read(['attributes'])[0]['attributes'][0]['tags']
        all_tags = {tag[0]: tuple(tag) for tag in all_tags}

        for group, (tag, count) in zip(result, (('a', 3), ('c', 1), ('d', 1), ('e', 2), ('g', 2))):
            self.assertEqual(group['attributes.mytags'], all_tags[tag])
            self.assertEqual(group['__count'], count)
            self.assertEqual(
                group['__extra_domain'],
                [('attributes.mytags', 'in', tag)],
            )
            # check that the value when we read the record match the value of the group
            property_values = [
                next(pro['value'] for pro in values['attributes'])
                for values in Model.search(group['__extra_domain']).read(['attributes'])
            ]
            self.assertTrue(all(tag in property_value for property_value in property_values))

        self.assertEqual(Model.search(result[-1]['__extra_domain']), self.message_4)
        self._check_many_falsy_group('mytags', result)
        self._check_domains_count(result)

        # now message 3 has *only* invalid tags, so it should be in the falsy group
        self.env.cr.execute(
            """
            UPDATE test_orm_message
               SET attributes = '{"mytags": ["invalid 1", "invalid 2", "invalid 3"]}'
             WHERE id = %s
            """,
            [self.message_3.id],
        )
        self.env.invalidate_all()

        with self.assertQueryCount(3):
            result = Model.formatted_read_group(
                domain=[('discussion', '!=', self.wrong_discussion_id)],
                aggregates=['__count'],
                groupby=['attributes.mytags'],
            )
        self.assertEqual(Model.search(result[-1]['__extra_domain']), self.message_3 | self.message_4)
        self._check_many_falsy_group('mytags', result)
        self._check_domains_count(result)

        # special case, there's no tag
        for tags in ([], False, None):
            self.message_1.attributes = [{
                'name': 'mytags',
                'type': 'tags',
                'value': tags,
                'tags': tags,
                'definition_changed': True,
            }]
            result = Model.formatted_read_group(
                domain=[('discussion', '!=', self.wrong_discussion_id)],
                aggregates=['__count'],
                groupby=['attributes.mytags'],
            )
            self.assertEqual(len(result), 1)
            self.assertFalse(result[0]['attributes.mytags'])
            self.assertEqual(result[0]['__count'], 4)
            self._check_domains_count(result)