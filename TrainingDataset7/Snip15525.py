def test_inlines_show_change_link_registered(self):
        "Inlines `show_change_link` for registered models when enabled."
        holder = Holder4.objects.create(dummy=1)
        item1 = Inner4Stacked.objects.create(dummy=1, holder=holder)
        item2 = Inner4Tabular.objects.create(dummy=1, holder=holder)
        items = (
            ("inner4stacked", item1.pk),
            ("inner4tabular", item2.pk),
        )
        response = self.client.get(
            reverse("admin:admin_inlines_holder4_change", args=(holder.pk,))
        )
        self.assertTrue(
            response.context["inline_admin_formset"].opts.has_registered_model
        )
        for model, pk in items:
            url = reverse("admin:admin_inlines_%s_change" % model, args=(pk,))
            self.assertContains(
                response, '<a href="%s" %s' % (url, INLINE_CHANGELINK_HTML)
            )