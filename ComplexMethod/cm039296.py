def test_all_tests_are_importable():
    # Ensure that for each contentful subpackage, there is a test directory
    # within it that is also a subpackage (i.e. a directory with __init__.py)

    HAS_TESTS_EXCEPTIONS = re.compile(
        r"""(?x)
        \.externals(\.|$)|
        \.tests(\.|$)|
        \._
        """
    )
    resource_modules = {
        "sklearn.datasets.data",
        "sklearn.datasets.descr",
        "sklearn.datasets.images",
    }
    sklearn_path = [os.path.dirname(sklearn.__file__)]
    lookup = {
        name: ispkg
        for _, name, ispkg in pkgutil.walk_packages(sklearn_path, prefix="sklearn.")
    }
    missing_tests = [
        name
        for name, ispkg in lookup.items()
        if ispkg
        and name not in resource_modules
        and not HAS_TESTS_EXCEPTIONS.search(name)
        and name + ".tests" not in lookup
    ]
    assert missing_tests == [], (
        "{0} do not have `tests` subpackages. "
        "Perhaps they require "
        "__init__.py or a meson.build "
        "in the parent "
        "directory".format(missing_tests)
    )