def test_pagination_render(self):
        objs = [Swallow(origin=f"Swallow {i}", load=i, speed=i) for i in range(1, 5)]
        Swallow.objects.bulk_create(objs)

        request = self.factory.get("/child/")
        request.user = self.superuser

        admin = SwallowAdmin(Swallow, custom_site)
        cl = admin.get_changelist_instance(request)
        template = Template(
            "{% load admin_list %}{% spaceless %}{% pagination cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": cl.opts})
        pagination_output = template.render(context)
        self.assertTrue(
            pagination_output.startswith(
                '<nav class="paginator" aria-labelledby="pagination">'
            )
        )
        self.assertInHTML(
            '<h2 id="pagination" class="visually-hidden">Pagination swallows</h2>',
            pagination_output,
        )
        self.assertTrue(pagination_output.endswith("</nav>"))
        self.assertInHTML(
            '<li><a role="button" href="" aria-current="page">1</a></li>',
            pagination_output,
        )
        self.assertInHTML(
            '<li><a role="button" href="?p=2">2</a></li>',
            pagination_output,
        )
        self.assertEqual(pagination_output.count('aria-current="page"'), 1)
        self.assertEqual(pagination_output.count('href=""'), 1)