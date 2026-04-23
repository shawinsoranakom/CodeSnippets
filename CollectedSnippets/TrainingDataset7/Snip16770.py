def get_delete_related(response):
            return (
                response.context["adminform"]
                .form.fields["sub_section"]
                .widget.can_delete_related
            )