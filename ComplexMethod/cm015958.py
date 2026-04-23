def _check_parametrization(
            parametrization,
            type_before_registration,
            type_after_registration,
            leave_parametrized=False,
            type_after_right_inverse=None,
        ):
            model = nn.Linear(2, 2)
            buf = torch.randn(2, 2)
            model.buf = torch.nn.Buffer(buf)
            if (
                type_before_registration == TwoTensor
                and type_after_registration == Tensor
            ):
                model._apply(lambda t: TwoTensor(t, t))
            initial_weight = model.weight.detach().clone()
            initial_weight_id = id(model.weight)
            initial_buf = model.buf.detach().clone()
            initial_buf_id = id(model.buf)
            type_original_weight = (
                type_before_registration
                if type_after_right_inverse is None
                else type_after_right_inverse
            )
            type_original_buf = (
                Tensor if type_original_weight is nn.Parameter else type_original_weight
            )
            type_after_removal_buf = (
                type_after_registration if leave_parametrized else type_original_buf
            )
            if leave_parametrized:
                if type_after_registration is Tensor:
                    type_after_removal_weight = nn.Parameter
                else:
                    type_after_removal_weight = type_after_registration
            else:
                type_after_removal_weight = type_original_weight

            parametrize.register_parametrization(model, "weight", parametrization())
            parametrize.register_parametrization(model, "buf", parametrization())
            self.assertTrue(hasattr(model, "parametrizations"))
            self.assertTrue(parametrize.is_parametrized(model))
            self.assertFalse(parametrize.is_parametrized(model, "bias"))
            # checks for weight
            self.assertTrue(parametrize.is_parametrized(model, "weight"))
            self.assertTrue(
                isinstance(model.parametrizations.weight.original, nn.Parameter)
            )
            self.assertTrue(
                type(model.parametrizations.weight.original) is type_original_weight
            )
            self.assertNotIn("weight", model._parameters)
            self.assertTrue(type(model.weight) is type_after_registration)
            # checks for buf
            self.assertTrue(parametrize.is_parametrized(model, "buf"))
            self.assertFalse(
                isinstance(model.parametrizations.buf.original, nn.Parameter)
            )
            self.assertTrue(
                type(model.parametrizations.buf.original) is type_original_buf
            )
            self.assertTrue(type(model.buf) is type_after_registration)
            parametrize.remove_parametrizations(
                model, "weight", leave_parametrized=leave_parametrized
            )
            parametrize.remove_parametrizations(
                model, "buf", leave_parametrized=leave_parametrized
            )
            self.assertFalse(hasattr(model, "parametrizations"))
            self.assertEqual(model.__class__, nn.Linear)
            # checks for weight
            self.assertTrue(type(model.weight) is type_after_removal_weight)
            self.assertTrue(isinstance(model.weight, nn.Parameter))
            self.assertEqual(id(model.weight), initial_weight_id)
            # checks for buf
            self.assertTrue(type(model.buf) is type_after_removal_buf)
            self.assertFalse(isinstance(model.buf, nn.Parameter))
            self.assertEqual(id(model.buf), initial_buf_id)
            if not leave_parametrized and type_after_right_inverse is None:
                self.assertEqual(model.weight, initial_weight)
                self.assertEqual(model.buf, initial_buf)