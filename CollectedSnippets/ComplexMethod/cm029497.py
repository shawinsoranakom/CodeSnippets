def test_template_test(app):
    bp = flask.Blueprint("bp", __name__)

    @bp.app_template_test()
    def is_boolean(value):
        return isinstance(value, bool)

    @bp.app_template_test
    def boolean_2(value):
        return isinstance(value, bool)

    @bp.app_template_test("my_boolean_custom_name")
    def boolean_3(value):
        return isinstance(value, bool)

    @bp.app_template_test(name="my_boolean_custom_name_2")
    def boolean_4(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix="/py")
    assert "is_boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["is_boolean"] == is_boolean
    assert app.jinja_env.tests["is_boolean"](False)

    assert "boolean_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean_2"] == boolean_2
    assert app.jinja_env.tests["boolean_2"](False)

    assert "my_boolean_custom_name" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name"] == boolean_3
    assert app.jinja_env.tests["my_boolean_custom_name"](False)

    assert "my_boolean_custom_name_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name_2"] == boolean_4
    assert app.jinja_env.tests["my_boolean_custom_name_2"](False)