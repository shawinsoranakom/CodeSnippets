def test(M):
            if M.size(0) < 5:
                raise AssertionError('this helper fn assumes M to be at least 5x5')
            M = M.to(device)

            ref_M_sdet, ref_M_logabsdet = reference_slogdet(M)

            test_single_det(M, (ref_M_sdet, ref_M_logabsdet), 'basic')
            if ref_M_logabsdet.exp().item() >= 1e-6:  # skip singular
                M_inv = M.inverse()
                test_single_det(M_inv, reference_slogdet(M_inv), 'inverse')

            test_single_det(M, (ref_M_sdet, ref_M_logabsdet), 'transpose')

            for x in [0, 2, 4]:
                for scale in [-2, -0.1, 0, 10]:
                    if scale > 0:
                        target = ref_M_sdet, ref_M_logabsdet + math.log(scale)
                    elif scale == 0:
                        target = torch.zeros_like(ref_M_sdet), torch.full_like(ref_M_logabsdet, -inf)
                    else:
                        target = ref_M_sdet.neg(), ref_M_logabsdet + math.log(-scale)

                    # dim 0
                    M_clone = M.clone()
                    M_clone[:, x] *= scale
                    test_single_det(M_clone, target, 'scale a row')
                    # dim 1
                    M_clone = M.clone()
                    M_clone[x, :] *= scale
                    test_single_det(M_clone, target, 'scale a column')

            for x1, x2 in [(0, 3), (4, 1), (3, 2)]:
                if x1 == x2:
                    raise AssertionError('x1 and x2 needs to be different for this test')
                target = torch.zeros_like(ref_M_sdet), torch.full_like(ref_M_logabsdet, -inf)
                # dim 0
                M_clone = M.clone()
                M_clone[:, x2] = M_clone[:, x1]
                test_single_det(M_clone, target, 'two rows are same')
                # dim 1
                M_clone = M.clone()
                M_clone[x2, :] = M_clone[x1, :]
                test_single_det(M_clone, target, 'two columns are same')

                for scale1, scale2 in [(0.3, -1), (0, 2), (10, 0.1)]:
                    det_scale = scale1 * scale2 * -1
                    if det_scale > 0:
                        target = ref_M_sdet, ref_M_logabsdet + math.log(det_scale)
                    elif det_scale == 0:
                        target = torch.zeros_like(ref_M_sdet), torch.full_like(ref_M_logabsdet, -inf)
                    else:
                        target = ref_M_sdet.neg(), ref_M_logabsdet + math.log(-det_scale)

                    # dim 0
                    M_clone = M.clone()
                    t = M_clone[:, x1] * scale1
                    M_clone[:, x1] += M_clone[:, x2] * scale2
                    M_clone[:, x2] = t
                    test_single_det(M_clone, target, 'exchanging rows')
                    # dim 1
                    M_clone = M.clone()
                    t = M_clone[x1, :] * scale1
                    M_clone[x1, :] += M_clone[x2, :] * scale2
                    M_clone[x2, :] = t
                    test_single_det(M_clone, target, 'exchanging columns')