def test_sitemap_item(self):
        """
        Check to make sure that the raw item is included with each
        Sitemap.get_url() url result.
        """
        test_sitemap = Sitemap()
        test_sitemap.items = TestModel.objects.order_by("pk").all

        def is_testmodel(url):
            return isinstance(url["item"], TestModel)

        item_in_url_info = all(map(is_testmodel, test_sitemap.get_urls()))
        self.assertTrue(item_in_url_info)