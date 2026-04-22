def test_name(self):
        """Test component name generation"""
        # Test a component defined in a module with no package
        component = components.declare_component("foo", url=URL)
        self.assertEqual("tests.streamlit.components_test.foo", component.name)

        # Test a component defined in __init__.py
        from tests.streamlit.component_test_data import component as init_component

        self.assertEqual(
            "tests.streamlit.component_test_data.foo",
            init_component.name,
        )

        # Test a component defined in a module within a package
        from tests.streamlit.component_test_data.outer_module import (
            component as outer_module_component,
        )

        self.assertEqual(
            "tests.streamlit.component_test_data.outer_module.foo",
            outer_module_component.name,
        )

        # Test a component defined in module within a nested package
        from tests.streamlit.component_test_data.nested.inner_module import (
            component as inner_module_component,
        )

        self.assertEqual(
            "tests.streamlit.component_test_data.nested.inner_module.foo",
            inner_module_component.name,
        )