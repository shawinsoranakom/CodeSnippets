def test_get_formset_kwargs(self):
        media_inline = MediaInline(Media, AdminSite())

        # Create a formset with default arguments
        formset = media_inline.get_formset(request)
        self.assertEqual(formset.max_num, DEFAULT_MAX_NUM)
        self.assertIs(formset.can_order, False)

        # Create a formset with custom keyword arguments
        formset = media_inline.get_formset(request, max_num=100, can_order=True)
        self.assertEqual(formset.max_num, 100)
        self.assertIs(formset.can_order, True)