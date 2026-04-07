def test_clear_removes_all_the_m2m_relationships(self):
        Membership.objects.create(person=self.jim, group=self.rock)
        Membership.objects.create(person=self.jane, group=self.rock)

        self.rock.members.clear()

        self.assertQuerySetEqual(self.rock.members.all(), [])