def test_context_available_in_response_for_partial_template(self):
        def sample_view(request):
            return HttpResponse(
                render_to_string("partial_examples.html#test-partial", {"foo": "bar"})
            )

        class PartialUrls:
            urlpatterns = [path("sample/", sample_view, name="sample-view")]

        with override_settings(ROOT_URLCONF=PartialUrls):
            response = self.client.get(reverse("sample-view"))

        self.assertContains(response, "TEST-PARTIAL-CONTENT")
        self.assertEqual(response.context.get("foo"), "bar")