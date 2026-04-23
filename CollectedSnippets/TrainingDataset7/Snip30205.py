def setUpTestData(cls):
        cls.qual1 = Qualification.objects.create(name="BA")
        cls.qual2 = Qualification.objects.create(name="BSci")
        cls.qual3 = Qualification.objects.create(name="MA")
        cls.qual4 = Qualification.objects.create(name="PhD")

        cls.teacher1 = Teacher.objects.create(name="Mr Cleese")
        cls.teacher2 = Teacher.objects.create(name="Mr Idle")
        cls.teacher3 = Teacher.objects.create(name="Mr Chapman")
        cls.teacher1.qualifications.add(cls.qual1, cls.qual2, cls.qual3, cls.qual4)
        cls.teacher2.qualifications.add(cls.qual1)
        cls.teacher3.qualifications.add(cls.qual2)

        cls.dept1 = Department.objects.create(name="English")
        cls.dept2 = Department.objects.create(name="Physics")
        cls.dept1.teachers.add(cls.teacher1, cls.teacher2)
        cls.dept2.teachers.add(cls.teacher1, cls.teacher3)