def test_update_with_joined_field_annotation(self):
        msg = "Joined field references are not permitted in this query"
        with register_lookup(CharField, Lower):
            for annotation in (
                F("data__name"),
                F("data__name__lower"),
                Lower("data__name"),
                Concat("data__name", "data__value"),
            ):
                with self.subTest(annotation=annotation):
                    with self.assertRaisesMessage(FieldError, msg):
                        RelatedPoint.objects.annotate(
                            new_name=annotation,
                        ).update(name=F("new_name"))