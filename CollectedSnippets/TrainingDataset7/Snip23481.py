def test_options(self):
        TaggedItemFormSet = generic_inlineformset_factory(
            TaggedItem,
            can_delete=False,
            exclude=["tag"],
            extra=3,
        )
        platypus = Animal.objects.create(
            common_name="Platypus", latin_name="Ornithorhynchus anatinus"
        )
        harmless = platypus.tags.create(tag="harmless")
        mammal = platypus.tags.create(tag="mammal")
        # Works without a queryset.
        formset = TaggedItemFormSet(instance=platypus)
        self.assertEqual(len(formset.forms), 5)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<input type="hidden" '
            'name="generic_relations-taggeditem-content_type-object_id-0-id" '
            'value="%s" '
            'id="id_generic_relations-taggeditem-content_type-object_id-0-id">'
            % harmless.pk,
        )
        self.assertEqual(formset.forms[0].instance, harmless)
        self.assertEqual(formset.forms[1].instance, mammal)
        self.assertIsNone(formset.forms[2].instance.pk)
        # A queryset can be used to alter display ordering.
        formset = TaggedItemFormSet(
            instance=platypus, queryset=TaggedItem.objects.order_by("-tag")
        )
        self.assertEqual(len(formset.forms), 5)
        self.assertEqual(formset.forms[0].instance, mammal)
        self.assertEqual(formset.forms[1].instance, harmless)
        self.assertIsNone(formset.forms[2].instance.pk)
        # A queryset that omits items.
        formset = TaggedItemFormSet(
            instance=platypus,
            queryset=TaggedItem.objects.filter(tag__startswith="harm"),
        )
        self.assertEqual(len(formset.forms), 4)
        self.assertEqual(formset.forms[0].instance, harmless)
        self.assertIsNone(formset.forms[1].instance.pk)