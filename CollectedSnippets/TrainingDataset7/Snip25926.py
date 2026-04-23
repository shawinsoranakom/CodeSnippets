def test_m2m_abstract_split(self):
        # Regression for #19236 - an abstract class with a 'split' method
        # causes a TypeError in add_lazy_relation
        m1 = RegressionModelSplit(name="1")
        m1.save()