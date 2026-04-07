def test_alternate_i18n_sitemap_xdefault(self):
        """
        A i18n sitemap index with x-default can be rendered.
        """
        response = self.client.get("/x-default/i18n.xml")
        url, pk = self.base_url, self.i18n_model.pk
        expected_urls = f"""
<url><loc>{url}/en/i18n/testmodel/{pk}/</loc><changefreq>never</changefreq><priority>0.5</priority>
<xhtml:link rel="alternate" hreflang="en" href="{url}/en/i18n/testmodel/{pk}/"/>
<xhtml:link rel="alternate" hreflang="pt" href="{url}/pt/i18n/testmodel/{pk}/"/>
<xhtml:link rel="alternate" hreflang="x-default" href="{url}/i18n/testmodel/{pk}/"/>
</url>
<url><loc>{url}/pt/i18n/testmodel/{pk}/</loc><changefreq>never</changefreq><priority>0.5</priority>
<xhtml:link rel="alternate" hreflang="en" href="{url}/en/i18n/testmodel/{pk}/"/>
<xhtml:link rel="alternate" hreflang="pt" href="{url}/pt/i18n/testmodel/{pk}/"/>
<xhtml:link rel="alternate" hreflang="x-default" href="{url}/i18n/testmodel/{pk}/"/>
</url>
""".replace("\n", "")
        expected_content = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            f'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f"{expected_urls}\n"
            f"</urlset>"
        )
        self.assertXMLEqual(response.text, expected_content)