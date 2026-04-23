def test_create_on_m2m_with_intermediate_model_value_required_fails(self):
        with self.assertRaises(IntegrityError):
            self.rock.nodefaultsnonulls.create(name="Test")