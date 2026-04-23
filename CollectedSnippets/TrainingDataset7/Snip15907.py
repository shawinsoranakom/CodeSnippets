def serve_template(request, *args, **kwargs):
            nonlocal user_agent
            user_agent = request.headers["User-Agent"]
            return serve(request, *args, **kwargs)