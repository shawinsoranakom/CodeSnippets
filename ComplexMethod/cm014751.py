def _test(training, batch_first, atol, rtol):
            def perm_fn(x):
                return x.transpose(1, 0) if batch_first else x

            model = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, dropout,
                                               batch_first=batch_first, device=device, dtype=dtype)

            if not training:
                if dropout != 0:
                    raise AssertionError(f"expected dropout == 0 when not training, got {dropout}")
                model = model.eval()

            # set constant weights of the model
            for p in model.parameters():
                x = p.data
                sz = x.view(-1).size(0)
                shape = x.shape
                x = torch.cos(torch.arange(0, sz).float().view(shape))
                p.data.copy_(x)

            # deterministic input
            encoder_input = torch.tensor([[[20., 30., 40., 50.]]], device=device, dtype=dtype)
            result = model(encoder_input)
            ref_output = torch.tensor([[[2.258703, 0.127985, -0.697881, 0.170862]]], device=device, dtype=dtype)
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
            # 0 values are NOT masked. This shouldn't mask anything.
            mask = torch.tensor([[0]], device=device) == 1
            # TODO: enable fast path for calls with a mask!
            result = model(encoder_input, src_key_padding_mask=mask)
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
            mask = torch.tensor([[1]], device=device) == 1
            result = model(encoder_input, src_key_padding_mask=mask)
            fast_path_device = result.is_cuda or result.is_cpu
            result = result.cpu().detach().numpy()
            # Non Fast Paths
            if training or not batch_first or TEST_WITH_CROSSREF or not fast_path_device:
                # We changed the semenatic, on the non fast path so that fully masked out rows return
                # 0 from attention thus NaNs should no longer be present and the output should be nonzero
                # due to skip connections
                self.assertTrue(not np.isnan(result).any())
            else:
                # Fast Paths
                self.assertTrue(np.isnan(result).all())


            # deterministic input
            encoder_input = perm_fn(torch.tensor([[[1., 2., 3., 4.]],
                                                  [[5., 6., 7., 8.]]], device=device, dtype=dtype))
            result = model(encoder_input)
            ref_output = perm_fn(torch.tensor([[[2.272644, 0.119035, -0.691669, 0.153486]],
                                               [[2.272644, 0.119035, -0.691669, 0.153486]]], device=device, dtype=dtype))
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
            # all 0 which is no masking
            mask = torch.tensor([[0, 0]], device=device) == 1
            result = model(encoder_input, src_key_padding_mask=mask)
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
            mask = torch.tensor([[1, 0]], device=device) == 1
            result = model(encoder_input, src_key_padding_mask=mask)
            ref_output = perm_fn(torch.tensor([[[2.301516, 0.092249, -0.679101, 0.103088]],
                                               [[2.301516, 0.092249, -0.679101, 0.103088]]], device=device, dtype=dtype))
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)

            # deterministic input
            encoder_input = perm_fn(torch.tensor([[[0.7462, 0.6653, 0.5679, 0.4891],
                                                   [0.5387, 0.1655, 0.3565, 0.0471]],
                                                  [[0.8335, 0.2799, 0.5031, 0.2947],
                                                   [0.1402, 0.0318, 0.7636, 0.1346]],
                                                  [[0.6333, 0.9344, 0.1376, 0.9938],
                                                   [0.8924, 0.2872, 0.6692, 0.2944]],
                                                  [[0.9897, 0.6915, 0.3154, 0.1733],
                                                   [0.8645, 0.3513, 0.3064, 0.0767]],
                                                  [[0.8117, 0.2366, 0.4838, 0.7881],
                                                   [0.3718, 0.4945, 0.9511, 0.0864]]], device=device, dtype=dtype))
            result = model(encoder_input)
            ref_output = perm_fn(torch.tensor([[[2.428589, 0.020835, -0.602055, -0.085249],
                                                [2.427987, 0.021213, -0.602496, -0.084103]],
                                               [[2.424689, 0.019155, -0.604793, -0.085672],
                                                [2.413863, 0.022211, -0.612486, -0.072490]],
                                               [[2.433774, 0.021598, -0.598343, -0.087548],
                                                [2.425104, 0.019748, -0.604515, -0.084839]],
                                               [[2.436185, 0.022682, -0.596625, -0.087261],
                                                [2.433556, 0.021891, -0.598509, -0.086832]],
                                               [[2.416246, 0.017512, -0.610712, -0.082961],
                                                [2.422901, 0.024187, -0.606178, -0.074929]]], device=device, dtype=dtype))
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)

            # all 0
            mask = torch.zeros([2, 5], device=device) == 1
            result = model(encoder_input, src_key_padding_mask=mask)
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
            mask[0, 1] = 1
            mask[1, 3] = 1
            mask[1, 4] = 1
            result = model(encoder_input, src_key_padding_mask=mask)
            ref_output = perm_fn(torch.tensor([[[2.429026, 0.020793, -0.601741, -0.085642],
                                                [2.428811, 0.021445, -0.601912, -0.084252]],
                                               [[2.425009, 0.019155, -0.604566, -0.085899],
                                                [2.415408, 0.02249 , -0.611415, -0.073]],
                                               [[2.434199, 0.021682, -0.598039, -0.087699],
                                                [2.42598, 0.019941, -0.603896, -0.085091]],
                                               [[2.436457, 0.022736, -0.59643 , -0.08736],
                                                [2.434021, 0.022093, -0.598179, -0.08679]],
                                               [[2.416531, 0.017498, -0.610513, -0.083181],
                                                [2.4242, 0.024653, -0.605266, -0.074959]]], device=device, dtype=dtype))
            self.assertEqual(result.shape, ref_output.shape)
            torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)

            # NestedTensor is only supported for the fast path
            # currently, which won't be used if training.
            if (batch_first and not training and
                    ('cuda' in str(device) or 'cpu' in str(device)) and not TEST_WITH_CROSSREF):
                encoder_input[0][-1] = torch.zeros_like(encoder_input[0][1])
                mask = torch.zeros(encoder_input.shape[:-1], device=device, dtype=torch.bool)
                mask[0][-1] = True

                nt = torch.nested.nested_tensor([encoder_input[0][:-1], encoder_input[1]], device=device)
                result = model(nt)
                ref_output = torch.tensor(
                    [
                        [
                            [2.4268184, 0.02042419, -0.603311, -0.08476824],
                            [2.423306, 0.01889652, -0.6057701, -0.08519465],
                            [2.431538, 0.02078694, -0.5999354, -0.08746159],
                            [2.4348664, 0.02212971, -0.5975677, -0.08733892],
                            [2.423133, 0.02097577, -0.60594773, -0.08113337],
                        ],
                        [
                            [2.4279876, 0.02121329, -0.60249615, -0.08410317],
                            [2.4138637, 0.02221113, -0.6124869, -0.07249016],
                            [2.4251041, 0.01974815, -0.6045152, -0.08483928],
                            [2.4335563, 0.0218913, -0.59850943, -0.08683228],
                            [2.4229012, 0.02418739, -0.6061784, -0.07492948],
                        ],
                    ],
                    device=device, dtype=dtype
                )
                result = result.to_padded_tensor(0)
                ref_output[0][-1] = torch.zeros_like(
                    ref_output[0][-1], device=device, dtype=dtype
                )
                result[0][-1] = torch.zeros_like(
                    result[0][-1], device=device, dtype=dtype
                )
                self.assertEqual(tuple(result.shape), tuple(ref_output.shape))
                if 'cuda' in device:
                    if dtype == torch.float:
                        atol = 2e-4
                        rtol = 4e-3
                    else:
                        atol = 7e-4
                        rtol = 2e-2
                    torch.testing.assert_close(result, ref_output, atol=atol, rtol=rtol)
                else:
                    torch.testing.assert_close(result, ref_output)