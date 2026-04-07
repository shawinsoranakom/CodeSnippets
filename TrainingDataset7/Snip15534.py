def test_inline_media_only_inline(self):
        holder = Holder3(dummy=13)
        holder.save()
        Inner3(dummy=42, holder=holder).save()
        change_url = reverse("admin:admin_inlines_holder3_change", args=(holder.id,))
        response = self.client.get(change_url)
        self.assertEqual(
            response.context["inline_admin_formsets"][0].media._js,
            [
                "admin/js/vendor/jquery/jquery.min.js",
                "my_awesome_inline_scripts.js",
                "custom_number.js",
                "admin/js/jquery.init.js",
                "admin/js/inlines.js",
            ],
        )
        self.assertContains(response, "my_awesome_inline_scripts.js")