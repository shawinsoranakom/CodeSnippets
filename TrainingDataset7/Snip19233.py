def _set_cache(self, request, msg):
        return UpdateCacheMiddleware(lambda req: HttpResponse(msg))(request)