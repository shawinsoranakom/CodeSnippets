def test_set_on_m2m_with_intermediate_model_value_required(self):
        self.rock.nodefaultsnonulls.set(
            [self.jim], through_defaults={"nodefaultnonull": 1}
        )
        self.assertEqual(self.rock.testnodefaultsornulls_set.get().nodefaultnonull, 1)
        self.rock.nodefaultsnonulls.set(
            [self.jim], through_defaults={"nodefaultnonull": 2}
        )
        self.assertEqual(self.rock.testnodefaultsornulls_set.get().nodefaultnonull, 1)
        self.rock.nodefaultsnonulls.set(
            [self.jim], through_defaults={"nodefaultnonull": 2}, clear=True
        )
        self.assertEqual(self.rock.testnodefaultsornulls_set.get().nodefaultnonull, 2)