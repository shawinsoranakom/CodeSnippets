def _test_namespace(ns, *skips):
            if isinstance(ns, object):
                ns_name = ns.__class__.__name__
            else:
                ns_name = ns.__name__
            skip_regexes = []
            for r in skips:
                if isinstance(r, str):
                    skip_regexes.append(re.compile(f'^{re.escape(r)}$'))
                else:
                    skip_regexes.append(r)

            for name in dir(ns):
                if name.startswith('_'):
                    continue
                if name in ['real', 'imag']:
                    y = torch.randn(1, dtype=torch.cfloat)
                    var = getattr(y, name)
                elif name in ["H", "mT", "mH"]:
                    y = torch.randn(1, 1)
                    var = getattr(y, name)
                else:
                    var = getattr(ns, name)
                if not isinstance(var, checked_types):
                    continue
                doc = var.__doc__
                has_doc = doc is not None and len(doc.strip()) > 0
                full_name = ns_name + '.' + name
                if any(r.match(name) for r in skip_regexes):
                    self.assertFalse(has_doc,
                                     f'New docs have been added for {full_name}, please remove '
                                     'it from the skipped list in TestTorch.test_doc')
                else:
                    self.assertTrue(has_doc, f'{full_name} is missing documentation')

            # FIXME: All of the following should be marked as expected failures
            # so that it is easier to tell when missing has been added.
            # FIXME: fix all the skipped ones below!
            test_namespace(torch.randn(1),  # noqa: F821
                           'as_strided_',
                           re.compile('^clamp_(min|max)_?$'),
                           'is_distributed',
                           'is_nonzero',
                           'is_same_size',
                           'log_softmax',
                           'map2_',
                           'new',
                           'reinforce',
                           'relu',
                           'relu_',
                           'prelu',
                           'resize',
                           'resize_as',
                           'softmax',
                           'split_with_sizes',
                           'unsafe_split_with_sizes',
                           '_autocast_to_fp16',
                           '_autocast_to_fp32',
                           )

            test_namespace(torch.nn)  # noqa: F821
            test_namespace(torch.nn.functional, 'assert_int_or_pair')