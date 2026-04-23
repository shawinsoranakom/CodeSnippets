def run(model0, model1, optimizer0, optimizer1, try_scaling_api):
                for i, (input, target) in enumerate(data):
                    optimizer0.zero_grad()
                    optimizer1.zero_grad()
                    output0 = model0(input)
                    output1 = model1(input.to(dev1))
                    loss0 = loss_fn(0.3 * output0 + 0.7 * output1.to(dev0), target)
                    loss1 = loss_fn(
                        0.6 * output0.to(dev1) - 0.4 * output1, target.to(dev1)
                    )

                    if try_scaling_api:
                        scaler.scale(loss0).backward(retain_graph=True)
                        scaler.scale(loss1).backward()
                        if i == skip_iter and scaler.is_enabled():
                            model1[1].weight.grad.data.fill_(float("inf"))

                        # As an additional stress test, separately unscale for one of the optimizers.
                        scaler.unscale_(optimizer0)

                        scaler.step(optimizer0)
                        scaler.step(optimizer1)

                        # Make sure the found_infs were collected properly across optimizers and devices.
                        if scaler.is_enabled():
                            self.assertTrue(
                                len(scaler._found_inf_per_device(optimizer0)) == 1
                            )
                            self.assertTrue(
                                len(scaler._found_inf_per_device(optimizer1)) == 1
                            )
                            self.assertTrue(
                                scaler._found_inf_per_device(optimizer0)[dev0].item()
                                == 0.0
                            )
                            self.assertTrue(
                                scaler._found_inf_per_device(optimizer1)[dev1].item()
                                == float(i == skip_iter)
                            )

                        scaler.update()
                    else:
                        loss0.backward(retain_graph=True)
                        loss1.backward()
                        optimizer0.step()
                        if (not scaler.is_enabled()) or (i != skip_iter):
                            optimizer1.step()