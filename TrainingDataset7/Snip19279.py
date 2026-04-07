def set_cache(request, lang, msg):
            def get_response(req):
                return HttpResponse(msg)

            translation.activate(lang)
            return UpdateCacheMiddleware(get_response)(request)