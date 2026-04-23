def my_function(method, post_data):
            if method == "POST":
                form = UserRegistration(post_data, auto_id=False)
            else:
                form = UserRegistration(auto_id=False)

            if form.is_valid():
                return "VALID: %r" % sorted(form.cleaned_data.items())

            t = Template(
                '<form method="post">'
                "{{ form }}"
                '<input type="submit" required>'
                "</form>"
            )
            return t.render(Context({"form": form}))