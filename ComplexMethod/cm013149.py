def instantiate_device_type_tests(
    generic_test_class,
    scope,
    except_for=None,
    only_for=None,
    include_lazy=False,
    allow_mps=False,
    allow_xpu=False,
):
    # Removes the generic test class from its enclosing scope so its tests
    # are not discoverable.
    del scope[generic_test_class.__name__]

    generic_members = set(generic_test_class.__dict__.keys())
    generic_tests = [x for x in generic_members if x.startswith("test")]

    # Creates device-specific test cases
    for base in get_desired_device_type_test_bases(
        except_for, only_for, include_lazy, allow_mps, allow_xpu
    ):
        class_name = generic_test_class.__name__ + base.device_type.upper()

        # type set to Any and suppressed due to unsupported runtime class:
        # https://github.com/python/mypy/wiki/Unsupported-Python-Features
        device_type_test_class: Any = type(class_name, (base, generic_test_class), {})

        # Arrange for setUpClass and tearDownClass methods defined both in the test template
        # class and in the generic base to be called. This allows device-parameterized test
        # classes to support setup and teardown.
        # NB: This should be done before instantiate_test() is called as that invokes setup.
        @classmethod
        def _setUpClass(cls):
            # This should always be called, whether or not the test class invokes
            # super().setUpClass(), to set the primary device.
            base.setUpClass()
            # We want to call the @classmethod defined in the generic base, but pass
            # it the device-specific class object (cls), hence the __func__ call.
            generic_test_class.setUpClass.__func__(cls)

        @classmethod
        def _tearDownClass(cls):
            # We want to call the @classmethod defined in the generic base, but pass
            # it the device-specific class object (cls), hence the __func__ call.
            generic_test_class.tearDownClass.__func__(cls)
            base.tearDownClass()

        device_type_test_class.setUpClass = _setUpClass
        device_type_test_class.tearDownClass = _tearDownClass

        for name in generic_members:
            if name in generic_tests:  # Instantiates test member
                test = getattr(generic_test_class, name)
                # XLA-compat shim (XLA's instantiate_test takes doesn't take generic_cls)
                sig = inspect.signature(device_type_test_class.instantiate_test)
                if len(sig.parameters) == 3:
                    # Instantiates the device-specific tests
                    device_type_test_class.instantiate_test(
                        name, copy.deepcopy(test), generic_cls=generic_test_class
                    )
                else:
                    device_type_test_class.instantiate_test(name, copy.deepcopy(test))
            # Ports non-test member. Setup / teardown have already been handled above
            elif name not in device_type_test_class.__dict__:
                nontest = getattr(generic_test_class, name)
                setattr(device_type_test_class, name, nontest)

        # Mimics defining the instantiated class in the caller's file
        # by setting its module to the given class's and adding
        # the module to the given scope.
        # This lets the instantiated class be discovered by unittest.
        device_type_test_class.__module__ = generic_test_class.__module__
        scope[class_name] = device_type_test_class

    # Delete the generic form of the test functions (e.g. TestFoo.test_bar()) so they're
    # not discoverable. This mutates the original class (TestFoo), which was removed from
    # scope above. At this point, device-specific tests (e.g. TestFooCUDA.test_bar_cuda)
    # have already been created and the generic forms are no longer needed.
    for name in generic_tests:
        delattr(generic_test_class, name)