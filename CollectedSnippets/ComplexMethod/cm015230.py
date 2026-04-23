def check_results(
            ref_results,
            test_results,
            ref_graph_inps,
            test_graph_inps,
            ref_inp,
            test_inp,
        ):
            ref_out, ref_grad = ref_results
            test_out, test_grad = test_results
            self.assertEqual(ref_grad, test_grad)
            if isinstance(ref_out, torch.Tensor):
                self.assertTrue(isinstance(test_out, torch.Tensor))
                ref_out, test_out = [ref_out], [test_out]
            for ref_o, test_o in zip(ref_out, test_out):
                if isinstance(ref_o, torch.Tensor):
                    self.assertEqual(ref_o.requires_grad, test_o.requires_grad)
                    self.assertEqual(ref_o.is_leaf, test_o.is_leaf)
                    ref_is_view_of_non_interm = is_in_base(
                        ref_o, ref_graph_inps
                    ) or is_in_base(ref_o, ref_out)
                    test_is_view_of_non_interm = is_in_base(
                        test_o, test_graph_inps
                    ) or is_in_base(test_o, test_out)
                    self.assertEqual(
                        ref_is_view_of_non_interm, test_is_view_of_non_interm
                    )
                    self.assertEqual(ref_o, test_o)
                    if test_mutation:
                        # This tests that autograd meta is set properly on the output we can
                        # mutate it.
                        ref_o.add_(2)
                        test_o.add_(2)
                        self.assertEqual(ref_o, test_o)
                        # Reverse the modification
                        ref_o.sub_(2)
                        test_o.sub_(2)
                        self.assertEqual(ref_o, test_o)
            for ref_i, test_i in zip(ref_inp, test_inp):
                if isinstance(ref_i, torch.Tensor):
                    self.assertEqual(ref_i.requires_grad, test_i.requires_grad)
                self.assertEqual(ref_i, test_i)