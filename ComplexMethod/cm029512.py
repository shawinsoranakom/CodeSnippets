def test_template_test(app):
    @app.template_test()
    def boolean(value):
        return isinstance(value, bool)

    assert "boolean" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean"] == boolean
    assert app.jinja_env.tests["boolean"](False)

    @app.template_test
    def boolean_2(value):
        return isinstance(value, bool)

    assert "boolean_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["boolean_2"] == boolean_2
    assert app.jinja_env.tests["boolean_2"](False)

    @app.template_test("my_boolean_custom_name")
    def boolean_3(value):
        return isinstance(value, bool)

    assert "my_boolean_custom_name" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name"] == boolean_3
    assert app.jinja_env.tests["my_boolean_custom_name"](False)

    @app.template_test(name="my_boolean_custom_name_2")
    def boolean_4(value):
        return isinstance(value, bool)

    assert "my_boolean_custom_name_2" in app.jinja_env.tests.keys()
    assert app.jinja_env.tests["my_boolean_custom_name_2"] == boolean_4
    assert app.jinja_env.tests["my_boolean_custom_name_2"](False)