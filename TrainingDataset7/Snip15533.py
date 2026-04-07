def test_inline_media_only_base(self):
        holder = Holder(dummy=13)
        holder.save()
        Inner(dummy=42, holder=holder).save()
        change_url = reverse("admin:admin_inlines_holder_change", args=(holder.id,))
        response = self.client.get(change_url)
        self.assertContains(response, "my_awesome_admin_scripts.js")