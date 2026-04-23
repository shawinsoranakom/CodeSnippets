def test_find_best_app(test_apps):
    class Module:
        app = Flask("appname")

    assert find_best_app(Module) == Module.app

    class Module:
        application = Flask("appname")

    assert find_best_app(Module) == Module.application

    class Module:
        myapp = Flask("appname")

    assert find_best_app(Module) == Module.myapp

    class Module:
        @staticmethod
        def create_app():
            return Flask("appname")

    app = find_best_app(Module)
    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        @staticmethod
        def create_app(**kwargs):
            return Flask("appname")

    app = find_best_app(Module)
    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        @staticmethod
        def make_app():
            return Flask("appname")

    app = find_best_app(Module)
    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        myapp = Flask("appname1")

        @staticmethod
        def create_app():
            return Flask("appname2")

    assert find_best_app(Module) == Module.myapp

    class Module:
        myapp = Flask("appname1")

        @staticmethod
        def create_app():
            return Flask("appname2")

    assert find_best_app(Module) == Module.myapp

    class Module:
        pass

    pytest.raises(NoAppException, find_best_app, Module)

    class Module:
        myapp1 = Flask("appname1")
        myapp2 = Flask("appname2")

    pytest.raises(NoAppException, find_best_app, Module)

    class Module:
        @staticmethod
        def create_app(foo, bar):
            return Flask("appname2")

    pytest.raises(NoAppException, find_best_app, Module)

    class Module:
        @staticmethod
        def create_app():
            raise TypeError("bad bad factory!")

    pytest.raises(TypeError, find_best_app, Module)