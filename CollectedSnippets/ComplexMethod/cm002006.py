def recursive_check(tuple_object, dict_object):
                    if isinstance(tuple_object, DynamicCache):  # MODIFIED PART START
                        for idx in range(len(tuple_object)):
                            recursive_check(tuple_object.layers[idx].conv_states, dict_object.layers[idx].conv_states)
                            recursive_check(
                                tuple_object.layers[idx].recurrent_states, dict_object.layers[idx].recurrent_states
                            )
                    elif isinstance(tuple_object, (list, tuple)):  # MODIFIED PART END
                        for tuple_iterable_value, dict_iterable_value in zip(tuple_object, dict_object):
                            recursive_check(tuple_iterable_value, dict_iterable_value)
                    elif isinstance(tuple_object, dict):
                        for tuple_iterable_value, dict_iterable_value in zip(
                            tuple_object.values(), dict_object.values()
                        ):
                            recursive_check(tuple_iterable_value, dict_iterable_value)
                    elif tuple_object is None:
                        return
                    else:
                        self.assertTrue(
                            torch.allclose(tuple_object, dict_object, atol=1e-5),
                            msg=(
                                "Tuple and dict output are not equal. Difference:"
                                f" {torch.max(torch.abs(tuple_object - dict_object))}. Tuple has `nan`:"
                                f" {torch.isnan(tuple_object).any()} and `inf`: {torch.isinf(tuple_object)}. Dict has"
                                f" `nan`: {torch.isnan(dict_object).any()} and `inf`: {torch.isinf(dict_object)}."
                            ),
                        )