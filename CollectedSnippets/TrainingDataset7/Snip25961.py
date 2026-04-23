def test_set_on_m2m_with_intermediate_model_callable_through_default(self):
        self.rock.members.set(
            [self.bob, self.jane],
            through_defaults={"invite_reason": lambda: "Why not?"},
        )
        self.assertSequenceEqual(self.rock.members.all(), [self.bob, self.jane])
        self.assertEqual(
            self.rock.membership_set.filter(
                invite_reason__startswith="Why not?",
            ).count(),
            2,
        )