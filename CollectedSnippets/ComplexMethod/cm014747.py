def check():
            self.assertEqual(len(parameter_dict), len(parameters))
            for (k1, (k2, m2)) in zip(parameters, parameter_dict.named_parameters()):
                self.assertEqual(k1, k2)
                self.assertIs(parameters[k1], m2)
            for k1, k2 in zip(parameters, parameter_dict):
                self.assertIs(parameters[k1], parameter_dict[k2])
            for k in parameter_dict:
                self.assertIs(parameter_dict[k], parameters[k])
            for k in parameter_dict:
                self.assertIs(parameter_dict[k], parameters[k])
            for k, v in parameter_dict.items():
                self.assertIs(v, parameters[k])
            for k1, m2 in zip(parameters, parameter_dict.values()):
                self.assertIs(parameters[k1], m2)
            for k in parameters:
                self.assertTrue(k in parameter_dict)