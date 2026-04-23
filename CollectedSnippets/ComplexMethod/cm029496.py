def test_template_filter(app):
    bp = flask.Blueprint("bp", __name__)

    @bp.app_template_filter()
    def my_reverse(s):
        return s[::-1]

    @bp.app_template_filter
    def my_reverse_2(s):
        return s[::-1]

    @bp.app_template_filter("my_reverse_custom_name_3")
    def my_reverse_3(s):
        return s[::-1]

    @bp.app_template_filter(name="my_reverse_custom_name_4")
    def my_reverse_4(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix="/py")
    assert "my_reverse" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse"] == my_reverse
    assert app.jinja_env.filters["my_reverse"]("abcd") == "dcba"

    assert "my_reverse_2" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_2"] == my_reverse_2
    assert app.jinja_env.filters["my_reverse_2"]("abcd") == "dcba"

    assert "my_reverse_custom_name_3" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_custom_name_3"] == my_reverse_3
    assert app.jinja_env.filters["my_reverse_custom_name_3"]("abcd") == "dcba"

    assert "my_reverse_custom_name_4" in app.jinja_env.filters.keys()
    assert app.jinja_env.filters["my_reverse_custom_name_4"] == my_reverse_4
    assert app.jinja_env.filters["my_reverse_custom_name_4"]("abcd") == "dcba"