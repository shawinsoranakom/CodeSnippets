def normal_view(request):
            template = engines["django"].from_string("Hello world")
            return HttpResponse(template.render())