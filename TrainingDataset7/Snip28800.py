def test_relations_related_objects(self):
        # Testing non hidden related objects
        self.assertEqual(
            sorted(
                field.related_query_name()
                for field in Relation._meta._relation_tree
                if not field.remote_field.field.remote_field.hidden
            ),
            sorted(
                [
                    "fk_abstract_rel",
                    "fk_base_rel",
                    "fk_concrete_rel",
                    "fo_abstract_rel",
                    "fo_base_rel",
                    "fo_concrete_rel",
                    "m2m_abstract_rel",
                    "m2m_base_rel",
                    "m2m_concrete_rel",
                ]
            ),
        )
        # Testing hidden related objects
        self.assertEqual(
            sorted(
                field.related_query_name() for field in BasePerson._meta._relation_tree
            ),
            sorted(
                [
                    "+",
                    "_model_meta_relating_basepeople_hidden_+",
                    "BasePerson_following_abstract+",
                    "BasePerson_following_abstract+",
                    "BasePerson_following_base+",
                    "BasePerson_following_base+",
                    "BasePerson_friends_abstract+",
                    "BasePerson_friends_abstract+",
                    "BasePerson_friends_base+",
                    "BasePerson_friends_base+",
                    "BasePerson_m2m_abstract+",
                    "BasePerson_m2m_base+",
                    "Relating_basepeople+",
                    "Relating_basepeople_hidden+",
                    "followers_abstract",
                    "followers_base",
                    "friends_abstract_rel_+",
                    "friends_base_rel_+",
                    "person",
                    "relating_basepeople",
                    "relating_baseperson",
                ]
            ),
        )
        self.assertEqual(
            [
                field.related_query_name()
                for field in AbstractPerson._meta._relation_tree
            ],
            [],
        )