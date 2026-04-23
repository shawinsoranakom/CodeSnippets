def test_constructor_autograd(self, device, layout):

        def specific_constructor(*args, **kwargs):
            if layout is torch.sparse_csr:
                return torch.sparse_csr_tensor(*args, **kwargs)
            elif layout is torch.sparse_csc:
                return torch.sparse_csc_tensor(*args, **kwargs)
            elif layout is torch.sparse_bsc:
                return torch.sparse_bsc_tensor(*args, **kwargs)
            elif layout is torch.sparse_bsr:
                return torch.sparse_bsr_tensor(*args, **kwargs)
            elif layout is torch.sparse_coo:
                return torch.sparse_coo_tensor(*args, **kwargs)
            else:
                raise NotImplementedError(layout)

        def generic_constructor(*args, **kwargs):
            if layout in {torch.sparse_csr, torch.sparse_csc, torch.sparse_bsr, torch.sparse_bsc}:
                kwargs.update(layout=layout)
                return torch.sparse_compressed_tensor(*args, **kwargs)
            elif layout is torch.sparse_coo:
                return torch.sparse_coo_tensor(*args, **kwargs)
            else:
                raise NotImplementedError(layout)

        if layout is torch.sparse_coo:
            constructors = (specific_constructor,)
        else:
            constructors = (specific_constructor, generic_constructor)

        for args, kwargs in self.generate_simple_inputs(
                layout, device=device, dtype=torch.float64,
                enable_batch=False,  # TODO: remove after gh-104868 is resolved
                output_tensor=False):
            values_offset = 1 if layout is torch.sparse_coo else 2

            for cnstr in constructors:
                for requires_grad in (False, True):
                    values = args[values_offset].detach().requires_grad_(requires_grad)
                    args = (*args[:values_offset], values, *args[values_offset + 1:])
                    kwargs_ = dict(kwargs)
                    args_ = args + (kwargs_.pop('size'),)

                    sparse = cnstr(*args, **kwargs)

                    self.assertEqual(sparse.requires_grad, requires_grad)

                    if requires_grad:
                        for masked in (False, True):
                            if layout is torch.sparse_coo:
                                torch.autograd.gradcheck(
                                    lambda i, v: cnstr(i, v, **kwargs).to_dense(masked_grad=masked),
                                    args, masked=masked)
                                torch.autograd.gradcheck(
                                    lambda i, v, sz: cnstr(i, v, sz, **kwargs_).to_dense(masked_grad=masked),
                                    args_, masked=masked)
                            else:
                                torch.autograd.gradcheck(
                                    lambda ci, pi, v: cnstr(ci, pi, v, **kwargs).to_dense(masked_grad=masked),
                                    args, masked=masked)
                                torch.autograd.gradcheck(
                                    lambda ci, pi, v, sz: cnstr(ci, pi, v, sz, **kwargs_).to_dense(masked_grad=masked),
                                    args_, masked=masked)