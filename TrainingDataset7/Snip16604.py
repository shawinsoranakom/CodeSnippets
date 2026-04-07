def test_readonly_post(self):
        data = {
            "title": "Django Got Readonly Fields",
            "content": "This is an incredible development.",
            "link_set-TOTAL_FORMS": "1",
            "link_set-INITIAL_FORMS": "0",
            "link_set-MAX_NUM_FORMS": "0",
        }
        response = self.client.post(reverse("admin:admin_views_post_add"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)
        p = Post.objects.get()
        self.assertEqual(p.posted, datetime.date.today())

        data["posted"] = "10-8-1990"  # some date that's not today
        response = self.client.post(reverse("admin:admin_views_post_add"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 2)
        p = Post.objects.order_by("-id")[0]
        self.assertEqual(p.posted, datetime.date.today())