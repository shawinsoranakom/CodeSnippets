def test_classbased_technical_404(self):
        response = self.client.get("/classbased404/")
        self.assertContains(
            response,
            '<th scope="row">Raised by:</th><td>view_tests.views.Http404View</td>',
            status_code=404,
            html=True,
        )