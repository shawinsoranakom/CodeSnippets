def get(self, request, *args, **kwargs):
        self.date_list, self.object_list, extra_context = self.get_dated_items()
        context = self.get_context_data(
            object_list=self.object_list, date_list=self.date_list, **extra_context
        )
        return self.render_to_response(context)