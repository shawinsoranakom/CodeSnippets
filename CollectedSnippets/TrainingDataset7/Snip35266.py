def test_unicode_handling(self):
        response = HttpResponse(
            '<p class="help">Some help text for the title (with Unicode ŠĐĆŽćžšđ)</p>'
        )
        self.assertContains(
            response,
            '<p class="help">Some help text for the title (with Unicode ŠĐĆŽćžšđ)</p>',
            html=True,
        )