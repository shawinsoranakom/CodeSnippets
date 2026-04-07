def setUpClass(cls):
        cls.field = ComplexField(widget=ComplexMultiWidget())
        super().setUpClass()