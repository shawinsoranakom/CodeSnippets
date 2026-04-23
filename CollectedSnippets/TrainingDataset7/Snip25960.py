def test_add_on_m2m_with_intermediate_model_callable_through_default(self):
        def invite_reason_callable():
            return "They were good at %s" % datetime.now()

        self.rock.members.add(
            self.bob,
            self.jane,
            through_defaults={"invite_reason": invite_reason_callable},
        )
        self.assertSequenceEqual(self.rock.members.all(), [self.bob, self.jane])
        self.assertEqual(
            self.rock.membership_set.filter(
                invite_reason__startswith="They were good at ",
            ).count(),
            2,
        )
        # invite_reason_callable() is called once.
        self.assertEqual(
            self.bob.membership_set.get().invite_reason,
            self.jane.membership_set.get().invite_reason,
        )