def test_RNN_dropout(self):
        # checking the assumption that cuDNN sticks dropout in between
        # RNN layers
        for p in (0, 0.276, 0.731, 1):
            for train in (True, False):
                for cuda in (True, False):
                    rnn = nn.RNN(10, 1000, 2, bias=False, dropout=p, nonlinearity='relu')
                    if cuda:
                        rnn.cuda()

                    if train:
                        rnn.train()
                    else:
                        rnn.eval()
                    rnn.weight_ih_l0.data.fill_(1)
                    rnn.weight_hh_l0.data.fill_(1)
                    rnn.weight_ih_l1.data.fill_(1)
                    rnn.weight_hh_l1.data.fill_(1)
                    input = torch.ones(1, 1, 10)
                    hx = torch.zeros(2, 1, 1000)
                    if cuda:
                        input = input.cuda()
                        hx = hx.cuda()

                    output, hy = rnn(input, hx)
                    self.assertEqual(output.data.min(), output.data.max())
                    output_val = output.data[0][0][0]
                    if p == 0 or not train:
                        self.assertEqual(output_val, 10000)
                    elif p == 1:
                        self.assertEqual(output_val, 0)
                    else:
                        self.assertGreater(output_val, 8000)
                        self.assertLess(output_val, 12000)
                        denorm_mod = (output_val * (1 - p)) % 10
                        self.assertLess(min(denorm_mod, 10 - denorm_mod), 1e-2)

                    self.assertEqual(hy[0].data.min(), hy[0].data.max())
                    self.assertEqual(hy[1].data.min(), hy[1].data.max())
                    self.assertEqual(hy.data[0][0][0], 10)
                    self.assertEqual(hy.data[1][0][0], output_val)