def test_language_for_item_i18n_sitemap(self):
        """
        A i18n sitemap index in which item can be chosen to be displayed for a
        lang or not.
        """
        only_pt = I18nTestModel.objects.create(name="Only for PT")
        response = self.client.get("/item-by-lang/i18n.xml")
        url, pk, only_pt_pk = self.base_url, self.i18n_model.pk, only_pt.pk
        expected_urls = (
            f"<url><loc>{url}/en/i18n/testmodel/{pk}/</loc>"
            f"<changefreq>never</changefreq><priority>0.5</priority></url>"
            f"<url><loc>{url}/pt/i18n/testmodel/{pk}/</loc>"
            f"<changefreq>never</changefreq><priority>0.5</priority></url>"
            f"<url><loc>{url}/pt/i18n/testmodel/{only_pt_pk}/</loc>"
            f"<changefreq>never</changefreq><priority>0.5</priority></url>"
        )
        expected_content = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            f'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f"{expected_urls}\n"
            f"</urlset>"
        )
        self.assertXMLEqual(response.text, expected_content)