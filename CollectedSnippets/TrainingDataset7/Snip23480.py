def test_output(self):
        GenericFormSet = generic_inlineformset_factory(TaggedItem, extra=1)
        formset = GenericFormSet()
        self.assertHTMLEqual(
            "".join(form.as_p() for form in formset.forms),
            """
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-tag">
            Tag:</label>
            <input id="id_generic_relations-taggeditem-content_type-object_id-0-tag"
                type="text"
                name="generic_relations-taggeditem-content_type-object_id-0-tag"
                maxlength="50"></p>
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            Delete:</label>
            <input type="checkbox"
                name="generic_relations-taggeditem-content_type-object_id-0-DELETE"
                id="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            <input type="hidden"
                name="generic_relations-taggeditem-content_type-object_id-0-id"
                id="id_generic_relations-taggeditem-content_type-object_id-0-id"></p>
            """,
        )
        formset = GenericFormSet(instance=Animal())
        self.assertHTMLEqual(
            "".join(form.as_p() for form in formset.forms),
            """
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-tag">
            Tag:</label>
            <input id="id_generic_relations-taggeditem-content_type-object_id-0-tag"
                type="text"
                name="generic_relations-taggeditem-content_type-object_id-0-tag"
                maxlength="50"></p>
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            Delete:</label>
            <input type="checkbox"
                name="generic_relations-taggeditem-content_type-object_id-0-DELETE"
                id="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            <input type="hidden"
                name="generic_relations-taggeditem-content_type-object_id-0-id"
                id="id_generic_relations-taggeditem-content_type-object_id-0-id"></p>
            """,
        )
        platypus = Animal.objects.create(
            common_name="Platypus",
            latin_name="Ornithorhynchus anatinus",
        )
        platypus.tags.create(tag="shiny")
        GenericFormSet = generic_inlineformset_factory(TaggedItem, extra=1)
        formset = GenericFormSet(instance=platypus)
        tagged_item_id = TaggedItem.objects.get(tag="shiny", object_id=platypus.id).id
        self.assertHTMLEqual(
            "".join(form.as_p() for form in formset.forms),
            """
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-tag">
            Tag:</label>
            <input id="id_generic_relations-taggeditem-content_type-object_id-0-tag"
                type="text"
                name="generic_relations-taggeditem-content_type-object_id-0-tag"
                value="shiny" maxlength="50"></p>
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            Delete:</label>
            <input type="checkbox"
                name="generic_relations-taggeditem-content_type-object_id-0-DELETE"
                id="id_generic_relations-taggeditem-content_type-object_id-0-DELETE">
            <input type="hidden"
                name="generic_relations-taggeditem-content_type-object_id-0-id"
                value="%s"
                id="id_generic_relations-taggeditem-content_type-object_id-0-id"></p>
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-1-tag">
            Tag:</label>
            <input id="id_generic_relations-taggeditem-content_type-object_id-1-tag"
                type="text"
                name="generic_relations-taggeditem-content_type-object_id-1-tag"
                maxlength="50"></p>
            <p><label
                for="id_generic_relations-taggeditem-content_type-object_id-1-DELETE">
            Delete:</label>
            <input type="checkbox"
                name="generic_relations-taggeditem-content_type-object_id-1-DELETE"
                id="id_generic_relations-taggeditem-content_type-object_id-1-DELETE">
            <input type="hidden"
                name="generic_relations-taggeditem-content_type-object_id-1-id"
                id="id_generic_relations-taggeditem-content_type-object_id-1-id"></p>
            """ % tagged_item_id,
        )
        lion = Animal.objects.create(common_name="Lion", latin_name="Panthera leo")
        formset = GenericFormSet(instance=lion, prefix="x")
        self.assertHTMLEqual(
            "".join(form.as_p() for form in formset.forms),
            """
            <p><label for="id_x-0-tag">Tag:</label>
            <input id="id_x-0-tag" type="text" name="x-0-tag" maxlength="50"></p>
            <p><label for="id_x-0-DELETE">Delete:</label>
            <input type="checkbox" name="x-0-DELETE" id="id_x-0-DELETE">
            <input type="hidden" name="x-0-id" id="id_x-0-id"></p>
            """,
        )