def test_insensitive_patterns_escape(self):
        r"""
        Special characters (e.g. %, _ and \) stored in database are
        properly escaped when using a case insensitive pattern lookup with an
        expression -- refs #16731
        """
        Employee.objects.bulk_create(
            [
                Employee(firstname="Johnny", lastname="%john"),
                Employee(firstname="Jean-Claude", lastname="claud_"),
                Employee(firstname="Jean-Claude", lastname="claude%"),
                Employee(firstname="Johnny", lastname="joh\\n"),
                Employee(firstname="Johnny", lastname="_ohn"),
            ]
        )
        claude = Employee.objects.create(firstname="Jean-Claude", lastname="claude")
        john = Employee.objects.create(firstname="Johnny", lastname="john")
        john_sign = Employee.objects.create(firstname="%Joh\\nny", lastname="%joh\\n")

        self.assertCountEqual(
            Employee.objects.filter(firstname__icontains=F("lastname")),
            [john_sign, john, claude],
        )
        self.assertCountEqual(
            Employee.objects.filter(firstname__istartswith=F("lastname")),
            [john_sign, john],
        )
        self.assertSequenceEqual(
            Employee.objects.filter(firstname__iendswith=F("lastname")),
            [claude],
        )