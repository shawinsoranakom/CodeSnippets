def test_add_template_global(app, app_ctx):
    @app.template_global()
    def get_stuff():
        return 42

    assert "get_stuff" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_stuff"] == get_stuff
    assert app.jinja_env.globals["get_stuff"](), 42

    rv = flask.render_template_string("{{ get_stuff() }}")
    assert rv == "42"

    @app.template_global
    def get_stuff_1():
        return "get_stuff_1"

    assert "get_stuff_1" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_stuff_1"] == get_stuff_1
    assert app.jinja_env.globals["get_stuff_1"](), "get_stuff_1"

    rv = flask.render_template_string("{{ get_stuff_1() }}")
    assert rv == "get_stuff_1"

    @app.template_global("my_get_stuff_custom_name_2")
    def get_stuff_2():
        return "get_stuff_2"

    assert "my_get_stuff_custom_name_2" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"] == get_stuff_2
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"](), "get_stuff_2"

    rv = flask.render_template_string("{{ my_get_stuff_custom_name_2() }}")
    assert rv == "get_stuff_2"

    @app.template_global(name="my_get_stuff_custom_name_3")
    def get_stuff_3():
        return "get_stuff_3"

    assert "my_get_stuff_custom_name_3" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"] == get_stuff_3
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"](), "get_stuff_3"

    rv = flask.render_template_string("{{ my_get_stuff_custom_name_3() }}")
    assert rv == "get_stuff_3"