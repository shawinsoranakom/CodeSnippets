def test_alters_data_propagation(self):
        class GrandParentLeft(AltersData):
            def my_method(self):
                return 42

            my_method.alters_data = True

        class ParentLeft(GrandParentLeft):
            def change_alters_data_method(self):
                return 63

            change_alters_data_method.alters_data = True

            def sub_non_callable_method(self):
                return 64

            sub_non_callable_method.alters_data = True

        class ParentRight(AltersData):
            def other_method(self):
                return 52

            other_method.alters_data = True

        class Child(ParentLeft, ParentRight):
            def my_method(self):
                return 101

            def other_method(self):
                return 102

            def change_alters_data_method(self):
                return 103

            change_alters_data_method.alters_data = False

            sub_non_callable_method = 104

        class GrandChild(Child):
            pass

        child = Child()
        self.assertIs(child.my_method.alters_data, True)
        self.assertIs(child.other_method.alters_data, True)
        self.assertIs(child.change_alters_data_method.alters_data, False)

        grand_child = GrandChild()
        self.assertIs(grand_child.my_method.alters_data, True)
        self.assertIs(grand_child.other_method.alters_data, True)
        self.assertIs(grand_child.change_alters_data_method.alters_data, False)

        c = Context({"element": grand_child})

        t = self.engine.from_string("{{ element.my_method }}")
        self.assertEqual(t.render(c), "")
        t = self.engine.from_string("{{ element.other_method }}")
        self.assertEqual(t.render(c), "")
        t = self.engine.from_string("{{ element.change_alters_data_method }}")
        self.assertEqual(t.render(c), "103")
        t = self.engine.from_string("{{ element.sub_non_callable_method }}")
        self.assertEqual(t.render(c), "104")