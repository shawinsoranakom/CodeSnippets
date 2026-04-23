def test_type_conversions(self):
        x = torch.randn(5, 5)
        self.assertIsInstance(x.float(), torch.FloatTensor)
        self.assertIsInstance(x.int(), torch.IntTensor)
        if torch.cuda.is_available():
            self.assertIsInstance(x.float().cuda(), torch.cuda.FloatTensor)
            self.assertIsInstance(x.int().cuda(), torch.cuda.IntTensor)
            self.assertIsInstance(x.int().cuda().cpu(), torch.IntTensor)
            if torch.cuda.device_count() >= 2:
                x2 = x.float().cuda(1)
                self.assertIsInstance(x2, torch.cuda.FloatTensor)
                self.assertIs(x2.get_device(), 1)
                x2 = x.float().cuda()
                self.assertIsInstance(x2, torch.cuda.FloatTensor)
                self.assertIs(x2.get_device(), 0)
                x2 = x2.cuda(1)
                self.assertIsInstance(x2, torch.cuda.FloatTensor)
                self.assertIs(x2.get_device(), 1)
                y = Variable(torch.randn(5).cuda(1), requires_grad=True)
                y.cpu().sum().backward()
                self.assertIs(y.grad.get_device(), 1)
                self.assertIs(y.long().get_device(), 1)

        for t in [
            torch.DoubleTensor,
            torch.FloatTensor,
            torch.IntTensor,
            torch.ByteTensor,
        ]:
            for y_var in (True, False):
                y = torch.randint(5, (5, 5), dtype=t.dtype)
                y = Variable(y) if y_var else y
                self.assertIsInstance(x.type(t), t)
                self.assertIsInstance(x.type_as(y), t)
                # TODO: t.dtype should work
                t_dtype = t().dtype
                self.assertIsInstance(x.type(t_dtype), t)
                self.assertIs(t_dtype, x.type(t_dtype).dtype)
                self.assertEqual(y.data_ptr(), y.type(t).data_ptr())
                if torch.cuda.is_available():
                    for x_cuda in (True, False):
                        for y_cuda in (True, False):
                            x_c = x.cuda() if x_cuda else x
                            y_c = y.cuda() if y_cuda else y
                            _, y_type = y_c.type().rsplit(".", 1)
                            y_typestr = ("torch.cuda." if y_cuda else "torch.") + y_type
                            self.assertEqual(y_c.type(), x_c.type(y_typestr).type())
                            self.assertIs(y_c.dtype, x_c.type(y_c.dtype).dtype)
                            self.assertEqual(
                                y_c.data_ptr(),
                                y_c.cuda().data_ptr() if y_cuda else y_c.data_ptr(),
                            )

        self._test_type_conversion_backward(lambda x: x)
        if torch.cuda.is_available():
            self._test_type_conversion_backward(lambda x: x.cuda())
            if torch.cuda.device_count() >= 2:
                # one of these has to be the non-default device
                self._test_type_conversion_backward(lambda x: x.cuda(0))
                self._test_type_conversion_backward(lambda x: x.cuda(1))