def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)