def test_manager_class_getitem(self):
        self.assertIs(models.Manager[Child1], models.Manager)