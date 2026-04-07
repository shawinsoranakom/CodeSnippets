def test_get_queryset_falls_back_to_pk_when_no_ordering_defined(self):
        # Product has no Meta.ordering, so the default queryset is not
        # totally ordered.
        self.assertIs(Product._default_manager.get_queryset().totally_ordered, False)

        ProductFormSet = modelformset_factory(Product, fields="__all__")
        formset = ProductFormSet()

        queryset = formset.get_queryset()
        self.assertEqual(queryset.query.order_by, ("pk",))