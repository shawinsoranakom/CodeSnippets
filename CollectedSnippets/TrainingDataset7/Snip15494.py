def test_readonly_stacked_inline_label(self):
        """Bug #13174."""
        holder = Holder.objects.create(dummy=42)
        Inner.objects.create(holder=holder, dummy=42, readonly="")
        response = self.client.get(
            reverse("admin:admin_inlines_holder_change", args=(holder.id,))
        )
        self.assertContains(response, "<label>Inner readonly label:</label>")