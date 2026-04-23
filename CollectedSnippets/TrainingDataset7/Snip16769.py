def get_change_related(response):
            return (
                response.context["adminform"]
                .form.fields["section"]
                .widget.can_change_related
            )