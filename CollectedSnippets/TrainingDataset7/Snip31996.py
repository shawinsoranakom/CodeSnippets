def response_delete_session(request):
            request.session = DatabaseSession()
            request.session.save(must_create=True)
            request.session.delete()
            return HttpResponse()