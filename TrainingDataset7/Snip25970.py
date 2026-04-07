def test_update_or_create_on_m2m_with_intermediate_model_value_required(self):
        self.rock.nodefaultsnonulls.update_or_create(
            name="Test", through_defaults={"nodefaultnonull": 1}
        )
        self.assertEqual(self.rock.testnodefaultsornulls_set.get().nodefaultnonull, 1)