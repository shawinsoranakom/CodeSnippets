def test_all_inline_media(self):
        holder = Holder2(dummy=13)
        holder.save()
        Inner2(dummy=42, holder=holder).save()
        change_url = reverse("admin:admin_inlines_holder2_change", args=(holder.id,))
        response = self.client.get(change_url)
        self.assertContains(response, "my_awesome_admin_scripts.js")
        self.assertContains(response, "my_awesome_inline_scripts.js")