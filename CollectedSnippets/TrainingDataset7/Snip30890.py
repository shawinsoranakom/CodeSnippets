def test_ticket_22429(self):
        sc1 = School.objects.create()
        st1 = Student.objects.create(school=sc1)

        sc2 = School.objects.create()
        st2 = Student.objects.create(school=sc2)

        cr = Classroom.objects.create(school=sc1)
        cr.students.add(st1)

        queryset = Student.objects.filter(~Q(classroom__school=F("school")))
        self.assertSequenceEqual(queryset, [st2])