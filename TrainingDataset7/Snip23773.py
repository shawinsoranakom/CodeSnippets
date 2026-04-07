def test_detail_by_pk_and_slug_mismatch_404(self):
        res = self.client.get(
            "/detail/author/bypkandslug/%s-scott-rosenberg/" % self.author1.pk
        )
        self.assertEqual(res.status_code, 404)