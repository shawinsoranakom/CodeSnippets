def message_extra_tags(self, request, selected):
        self.message_user(request, "Test tags", extra_tags="extra_tag")