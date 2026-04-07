def test_m2m_then_m2m(self):
        with self.assertNumQueries(3):
            # When we prefetch the teachers, and force the query, we don't want
            # the default manager on teachers to immediately get all the
            # related qualifications, since this will do one query per teacher.
            qs = Department.objects.prefetch_related("teachers")
            depts = "".join(
                "%s department: %s\n"
                % (dept.name, ", ".join(str(t) for t in dept.teachers.all()))
                for dept in qs
            )

            self.assertEqual(
                depts,
                "English department: Mr Cleese (BA, BSci, MA, PhD), Mr Idle (BA)\n"
                "Physics department: Mr Cleese (BA, BSci, MA, PhD), Mr Chapman "
                "(BSci)\n",
            )