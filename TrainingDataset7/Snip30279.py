def test_model_subclass_proxy(self):
        """
        Deleting an instance of a model proxying a multi-table inherited
        subclass should cascade delete down the whole inheritance chain (see
        #18083).
        """
        instance = ConcreteModelSubclassProxy.objects.create()
        instance.delete()
        self.assertEqual(0, ConcreteModelSubclassProxy.objects.count())
        self.assertEqual(0, ConcreteModelSubclass.objects.count())
        self.assertEqual(0, ConcreteModel.objects.count())