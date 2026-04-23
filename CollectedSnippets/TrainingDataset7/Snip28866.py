def test_model_with_evaluate_method(self):
        """
        You can filter by objects that have an 'evaluate' attr
        """
        dept = Department.objects.create(pk=1, name="abc")
        dept.evaluate = "abc"
        Worker.objects.filter(department=dept)