def test_inverted_q_across_relations(self):
        """
        When a trimmable join is specified in the query (here school__), the
        ORM detects it and removes unnecessary joins. The set of reusable joins
        are updated after trimming the query so that other lookups don't
        consider that the outer query's filters are in effect for the subquery
        (#26551).
        """
        springfield_elementary = School.objects.create()
        hogward = School.objects.create()
        Student.objects.create(school=springfield_elementary)
        hp = Student.objects.create(school=hogward)
        Classroom.objects.create(school=hogward, name="Potion")
        Classroom.objects.create(school=springfield_elementary, name="Main")
        qs = Student.objects.filter(
            ~(
                Q(school__classroom__name="Main")
                & Q(school__classroom__has_blackboard=None)
            )
        )
        self.assertSequenceEqual(qs, [hp])