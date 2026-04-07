def test_localize_pk_shortcut(self):
        """
        The "View on Site" link is correct for locales that use thousand
        separators.
        """
        holder = Holder.objects.create(pk=123456789, dummy=42)
        inner = Inner.objects.create(pk=987654321, holder=holder, dummy=42, readonly="")
        response = self.client.get(
            reverse("admin:admin_inlines_holder_change", args=(holder.id,))
        )
        inner_shortcut = "r/%s/%s/" % (
            ContentType.objects.get_for_model(inner).pk,
            inner.pk,
        )
        self.assertContains(response, inner_shortcut)