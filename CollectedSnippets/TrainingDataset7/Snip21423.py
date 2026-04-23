def test_patterns_escape(self):
        r"""
        Special characters (e.g. %, _ and \) stored in database are
        properly escaped when using a pattern lookup with an expression
        refs #16731
        """
        Employee.objects.bulk_create(
            [
                Employee(firstname="Johnny", lastname="%John"),
                Employee(firstname="Jean-Claude", lastname="Claud_"),
                Employee(firstname="Jean-Claude", lastname="Claude%"),
                Employee(firstname="Johnny", lastname="Joh\\n"),
                Employee(firstname="Johnny", lastname="_ohn"),
                # These names have regex characters that must be escaped by
                # backends (like MongoDB) that use regex matching rather than
                # LIKE.
                Employee(firstname="Johnny", lastname="^Joh"),
                Employee(firstname="Johnny", lastname="Johnny$"),
                Employee(firstname="Johnny", lastname="Joh."),
                Employee(firstname="Johnny", lastname="[J]ohnny"),
                Employee(firstname="Johnny", lastname="(J)ohnny"),
                Employee(firstname="Johnny", lastname="J*ohnny"),
                Employee(firstname="Johnny", lastname="J+ohnny"),
                Employee(firstname="Johnny", lastname="J?ohnny"),
                Employee(firstname="Johnny", lastname="J{1}ohnny"),
                Employee(firstname="Johnny", lastname="J|ohnny"),
                Employee(firstname="Johnny", lastname="J-ohnny"),
            ]
        )
        claude = Employee.objects.create(firstname="Jean-Claude", lastname="Claude")
        john = Employee.objects.create(firstname="Johnny", lastname="John")
        john_sign = Employee.objects.create(firstname="%Joh\\nny", lastname="%Joh\\n")

        self.assertCountEqual(
            Employee.objects.filter(firstname__contains=F("lastname")),
            [john_sign, john, claude],
        )
        self.assertCountEqual(
            Employee.objects.filter(firstname__startswith=F("lastname")),
            [john_sign, john],
        )
        self.assertSequenceEqual(
            Employee.objects.filter(firstname__endswith=F("lastname")),
            [claude],
        )