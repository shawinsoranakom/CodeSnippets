def sample_view(request):
            return HttpResponse(
                render_to_string("partial_examples.html#test-partial", {"foo": "bar"})
            )