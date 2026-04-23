def test_set_state_with_pk_specified(self):
        state_ca = State(two_letter_code="CA")
        state_ny = State(two_letter_code="NY")
        State.objects.bulk_create([state_ca])
        state_ny.save()
        # Objects save via bulk_create() and save() should have equal state.
        self.assertEqual(state_ca._state.adding, state_ny._state.adding)
        self.assertEqual(state_ca._state.db, state_ny._state.db)