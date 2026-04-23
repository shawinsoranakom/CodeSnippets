def test_template_global(app):
    bp = flask.Blueprint("bp", __name__)

    @bp.app_template_global()
    def get_answer():
        return 42

    @bp.app_template_global
    def get_stuff_1():
        return "get_stuff_1"

    @bp.app_template_global("my_get_stuff_custom_name_2")
    def get_stuff_2():
        return "get_stuff_2"

    @bp.app_template_global(name="my_get_stuff_custom_name_3")
    def get_stuff_3():
        return "get_stuff_3"

    # Make sure the function is not in the jinja_env already
    assert "get_answer" not in app.jinja_env.globals.keys()
    app.register_blueprint(bp)

    # Tests
    assert "get_answer" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_answer"] is get_answer
    assert app.jinja_env.globals["get_answer"]() == 42

    assert "get_stuff_1" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["get_stuff_1"] == get_stuff_1
    assert app.jinja_env.globals["get_stuff_1"](), "get_stuff_1"

    assert "my_get_stuff_custom_name_2" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"] == get_stuff_2
    assert app.jinja_env.globals["my_get_stuff_custom_name_2"](), "get_stuff_2"

    assert "my_get_stuff_custom_name_3" in app.jinja_env.globals.keys()
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"] == get_stuff_3
    assert app.jinja_env.globals["my_get_stuff_custom_name_3"](), "get_stuff_3"

    with app.app_context():
        rv = flask.render_template_string("{{ get_answer() }}")
        assert rv == "42"

        rv = flask.render_template_string("{{ get_stuff_1() }}")
        assert rv == "get_stuff_1"

        rv = flask.render_template_string("{{ my_get_stuff_custom_name_2() }}")
        assert rv == "get_stuff_2"

        rv = flask.render_template_string("{{ my_get_stuff_custom_name_3() }}")
        assert rv == "get_stuff_3"