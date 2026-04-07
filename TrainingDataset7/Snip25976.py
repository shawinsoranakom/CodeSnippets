def test_set_on_m2m_with_intermediate_model_value_required_fails(self):
        with self.assertRaises(IntegrityError):
            self.rock.nodefaultsnonulls.set([self.jim])