def test_initial(self):
        quartz = Mineral.objects.create(name="Quartz", hardness=7)
        GenericFormSet = generic_inlineformset_factory(TaggedItem, extra=1)
        ctype = ContentType.objects.get_for_model(quartz)
        initial_data = [
            {
                "tag": "lizard",
                "content_type": ctype.pk,
                "object_id": quartz.pk,
            }
        ]
        formset = GenericFormSet(initial=initial_data)
        self.assertEqual(formset.forms[0].initial, initial_data[0])