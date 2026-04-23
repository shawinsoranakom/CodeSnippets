def test_RNN_dropout_state(self):
        for p in (0, 0.1234):
            for train in (True, False):
                for cuda in (True, False):
                    rnn = nn.RNN(100, 100, 2, bias=False, dropout=p, nonlinearity='relu')
                    if cuda:
                        rnn.cuda()

                    if train:
                        rnn.train()
                    else:
                        rnn.eval()
                    input = torch.rand(1, 1, 100)
                    hx = torch.rand(2, 1, 100)
                    if cuda:
                        input = input.cuda()
                        hx = hx.cuda()

                    output1, hy1 = rnn(input, hx)
                    output2, hy2 = rnn(input, hx)

                    buf = io.BytesIO()
                    rnn_pickle = torch.save(rnn, buf)
                    buf.seek(0)
                    # weights_only=False as this is legacy code that saves the model
                    rnn2 = torch.load(buf, weights_only=False)
                    rnn2.flatten_parameters()
                    output3, hy3 = rnn2(input, hx)

                    if p == 0 or not train:
                        self.assertEqual(output1, output2)
                        self.assertEqual(output1, output3)
                        self.assertEqual(hy1, hy2)
                        self.assertEqual(hy1, hy3)
                    else:
                        self.assertNotEqual(output1, output2)
                        self.assertNotEqual(output1, output3)
                        self.assertNotEqual(hy1, hy2)
                        self.assertNotEqual(hy1, hy3)