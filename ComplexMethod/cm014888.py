def test_instance_norm(self):
        def helper(shape, eps=1, momentum=0.1, wts=False, channels_last=False, track_running_stats=True, test_module=False):

            import numpy as np
            np.random.seed(332)
            arr = (256 - 128) * np.random.random_sample(size=shape) + 128
            cpu_x = torch.tensor(arr, device='cpu', dtype=torch.float, requires_grad=True)
            if (channels_last):
                cpu_x = cpu_x.to(memory_format=torch.channels_last)
                cpu_x.retain_grad()
            x = cpu_x.detach().clone().to('mps').requires_grad_()

            mean_shape = [shape[1]]
            cpu_running_mean = None
            cpu_running_var = None
            running_mean = None
            running_var = None
            if (track_running_stats):
                mean_arr = (240 - 140) * np.random.random_sample(size=mean_shape) + 140
                cpu_running_mean = torch.tensor(mean_arr, device='cpu', dtype=torch.float)
                var_arr = 32 * np.random.random_sample(size=mean_shape)
                cpu_running_var = torch.tensor(var_arr, device='cpu', dtype=torch.float)
                running_mean = cpu_running_mean.detach().clone().to('mps')
                running_var = cpu_running_var.detach().clone().to('mps')

            weight = None
            cpu_weight = None
            bias = None
            cpu_bias = None
            if (wts):
                cpu_weight = torch.randn(mean_shape, device='cpu', dtype=torch.float, requires_grad=True)
                weight = cpu_weight.detach().clone().to('mps').requires_grad_()
                cpu_bias = torch.randn(mean_shape, device='cpu', dtype=torch.float, requires_grad=True)
                bias = cpu_bias.detach().clone().to('mps').requires_grad_()

            y = None
            ref_y = None

            if (not test_module):
                ref_y = torch.nn.functional.instance_norm(cpu_x, cpu_running_mean, cpu_running_var,
                                                          weight=cpu_weight,
                                                          bias=cpu_bias,
                                                          momentum=momentum, eps=eps)
                y = torch.nn.functional.instance_norm(x, running_mean, running_var,
                                                      weight=weight,
                                                      bias=bias,
                                                      momentum=momentum, eps=eps)

            else:

                instancenorm_op = None
                mps_instancenorm_op = None

                if (len(shape) == 3):
                    instancenorm_op = torch.nn.InstanceNorm1d(shape[1],
                                                              eps=eps,
                                                              momentum=momentum,
                                                              affine=wts,
                                                              track_running_stats=track_running_stats,
                                                              device='cpu')
                    mps_instancenorm_op = torch.nn.InstanceNorm1d(shape[1],
                                                                  eps=eps,
                                                                  momentum=momentum,
                                                                  affine=wts,
                                                                  track_running_stats=track_running_stats,
                                                                  device='mps')
                elif (len(shape) == 4):
                    instancenorm_op = torch.nn.InstanceNorm2d(shape[1],
                                                              eps=eps,
                                                              momentum=momentum,
                                                              affine=wts,
                                                              track_running_stats=track_running_stats,
                                                              device='cpu')
                    mps_instancenorm_op = torch.nn.InstanceNorm2d(shape[1],
                                                                  eps=eps,
                                                                  momentum=momentum,
                                                                  affine=wts,
                                                                  track_running_stats=track_running_stats,
                                                                  device='mps')
                elif (len(shape) == 5):
                    instancenorm_op = torch.nn.InstanceNorm3d(shape[1],
                                                              eps=eps,
                                                              momentum=momentum,
                                                              affine=wts,
                                                              track_running_stats=track_running_stats,
                                                              device='cpu')
                    mps_instancenorm_op = torch.nn.InstanceNorm3d(shape[1],
                                                                  eps=eps,
                                                                  momentum=momentum,
                                                                  affine=wts,
                                                                  track_running_stats=track_running_stats,
                                                                  device='mps')

                if (track_running_stats):
                    instancenorm_op.running_mean = cpu_running_mean
                    instancenorm_op.running_var = cpu_running_var
                    mps_instancenorm_op.running_mean = running_mean
                    mps_instancenorm_op.running_var = running_var
                if (wts):
                    instancenorm_op.weight = torch.nn.Parameter(cpu_weight)
                    instancenorm_op.bias = torch.nn.Parameter(cpu_bias)
                    mps_instancenorm_op.weight = torch.nn.Parameter(weight)
                    mps_instancenorm_op.bias = torch.nn.Parameter(bias)

                ref_y = instancenorm_op(cpu_x)
                y = mps_instancenorm_op(x)

            self.assertEqual(y, ref_y)
            if (not test_module):
                self.assertEqual(running_mean, cpu_running_mean)
                self.assertEqual(running_var, cpu_running_var)
            else:
                self.assertEqual(mps_instancenorm_op.running_mean, instancenorm_op.running_mean)
                self.assertEqual(mps_instancenorm_op.running_var, instancenorm_op.running_var)

            cpu_grad = torch.randn(ref_y.shape)
            grad = cpu_grad.to('mps')
            ref_y.backward(gradient=cpu_grad)
            y.backward(gradient=grad)

            self.assertEqual(x.grad, cpu_x.grad)
            if (wts):
                if (not test_module):
                    self.assertEqual(weight.grad, cpu_weight.grad)
                    self.assertEqual(bias.grad, cpu_bias.grad)
                else:
                    self.assertEqual(mps_instancenorm_op.weight.grad, instancenorm_op.weight.grad)
                    self.assertEqual(mps_instancenorm_op.bias.grad, instancenorm_op.bias.grad)

        for shape in [(2, 3, 2, 2), (2, 3, 2, 2, 2), (2, 3, 2)]:
            for test_module in [False, True]:
                for track_running_stats in [True, False]:
                    for channels_last in [False]:
                        if (channels_last and len(shape) != 4):
                            continue
                        # Running stats must be tracked in eval mode
                        if (track_running_stats):
                            helper(shape, eps=0, momentum=1, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                            helper(shape, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                            helper(shape, eps=1e-05, momentum=0.1, wts=False, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                            helper(shape, eps=0, momentum=1.0, wts=False, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                            helper(shape, eps=1, momentum=1, wts=True, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                            helper(shape, eps=3, momentum=0.67, wts=True, channels_last=channels_last,
                                   track_running_stats=track_running_stats, test_module=test_module)
                        helper(shape, eps=1e-05, momentum=0.1, wts=False, channels_last=channels_last,
                               track_running_stats=track_running_stats, test_module=test_module)
                        helper(shape, eps=0, momentum=1.0, wts=False, channels_last=channels_last,
                               track_running_stats=track_running_stats, test_module=test_module)
                        helper(shape, eps=1, momentum=1, wts=True, channels_last=channels_last,
                               track_running_stats=track_running_stats, test_module=test_module)
                        helper(shape, eps=3, momentum=0.67, wts=True, channels_last=channels_last,
                               track_running_stats=track_running_stats, test_module=test_module)