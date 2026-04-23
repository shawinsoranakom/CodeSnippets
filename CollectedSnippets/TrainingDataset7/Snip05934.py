def get(self, request, *args, **kwargs):
        """
        Return a JsonResponse with search results as defined in
        serialize_result(), by default:
        {
            results: [{id: "123" text: "foo"}],
            pagination: {more: true}
        }
        """
        (
            self.term,
            self.model_admin,
            self.source_field,
            to_field_name,
        ) = self.process_request(request)

        if not self.has_perm(request):
            raise PermissionDenied

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                "results": [
                    self.serialize_result(obj, to_field_name)
                    for obj in context["object_list"]
                ],
                "pagination": {"more": context["page_obj"].has_next()},
            }
        )