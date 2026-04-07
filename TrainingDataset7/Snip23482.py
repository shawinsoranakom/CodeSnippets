def test_get_queryset_ordering(self):
        """
        BaseGenericInlineFormSet.get_queryset() adds default ordering, if
        needed.
        """
        inline_formset = generic_inlineformset_factory(TaggedItem, exclude=("tag",))
        formset = inline_formset(instance=Gecko.objects.create())
        self.assertIs(formset.get_queryset().ordered, True)