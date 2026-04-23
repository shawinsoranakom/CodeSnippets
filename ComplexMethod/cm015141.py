def neg_dim_test(self):
        if isinstance(tensor_arg, list):
            if METHOD in types or INPLACE_METHOD in types:
                raise AssertionError("METHOD and INPLACE_METHOD should not be in types for list tensor_arg")
            x = [torch.randn(arg) for arg in tensor_arg]
            ndim = len(tensor_arg[-1])
        else:
            x = torch.randn(*tensor_arg)
            ndim = len(tensor_arg)
        ndim += extra_dim

        n_dim_to_test = sum(e is DIM_ARG for e in arg_constr())

        for dims_val in combinations(range(ndim), n_dim_to_test):
            arg = arg_constr()
            arg_neg = copy.deepcopy(arg)
            idx = 0
            for i, v in enumerate(arg):
                if v is DIM_ARG:
                    arg[i] = dims_val[idx]
                    arg_neg[i] = dims_val[idx] - ndim
                    idx += 1

            if METHOD in types:
                a = getattr(x, name)(*arg)
                b = getattr(x, name)(*arg_neg)
                self.assertEqual(a, b)

            if INPLACE_METHOD in types:
                a = x.clone()
                getattr(a, name + '_')(*arg)
                b = x.clone()
                getattr(b, name + '_')(*arg_neg)
                self.assertEqual(a, b)

            if FUNCTIONAL in types:
                a = getattr(torch, name)(x, *arg)
                b = getattr(torch, name)(x, *arg_neg)
                self.assertEqual(a, b)