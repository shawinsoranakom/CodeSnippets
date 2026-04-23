def generate_input():
                # If valid_channels_dim=False, add 1 to make channels dim indivisible by upscale_factor ** 2.
                channels = random.randint(1, 4) * upscale_factor ** 2 + (0 if valid_channels_dim else 1)
                height = random.randint(5, 10)
                width = random.randint(5, 10)

                if num_input_dims == 1:
                    input = torch.rand(channels, requires_grad=True, device='mps')
                    if not is_contiguous:
                        raise AssertionError("1D input should be contiguous")
                elif num_input_dims == 2:
                    input = torch.rand(width, height, requires_grad=True, device='mps').T
                    if is_contiguous:
                        input = input.contiguous()
                else:
                    batch_sizes = [random.randint(1, 3) for _ in range(num_input_dims - 3)]
                    input = torch.rand(*batch_sizes, channels, width, height, requires_grad=True, device='mps')
                    input = input.transpose(-1, -2)
                    if is_contiguous:
                        input = input.contiguous()

                if not is_contiguous and len(input.reshape(-1)) > 0:
                    if input.is_contiguous():
                        raise AssertionError("expected non-contiguous input")

                input = input.detach().clone()
                input.requires_grad = True
                return input