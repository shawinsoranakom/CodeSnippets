def get_cond_response(req):
            return ConditionalGetMiddleware(get_response)(req)