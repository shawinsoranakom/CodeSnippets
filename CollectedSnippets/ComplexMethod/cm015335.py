def generate_tensor():
            numpy_dtype = dtype if dtype != torch.bfloat16 else torch.float32
            # transposed tensors
            for perm1, perm2 in itertools.product(
                itertools.permutations((0, 1, 2)), repeat=2
            ):
                for perm3 in itertools.permutations((0, 1)):
                    b1 = (
                        make_tensor(
                            (num_batches, M, N),
                            dtype=dtype,
                            device=device,
                            low=-1,
                            high=1,
                        )
                        * 0.1
                    )
                    b2 = (
                        make_tensor(
                            (num_batches, N, O),
                            dtype=dtype,
                            device=device,
                            low=-1,
                            high=1,
                        )
                        * 0.1
                    )
                    b1 = b1.permute(perm1).contiguous().permute(invert_perm(perm1))
                    b2 = b2.permute(perm2).contiguous().permute(invert_perm(perm2))
                    ref = (
                        torch.from_numpy(
                            b1.to(numpy_dtype).cpu().numpy()
                            @ b2.to(numpy_dtype).cpu().numpy()
                        )
                        .to(device=device, dtype=dtype)
                        .sum(0)
                    )
                    out_tensor = (
                        torch.zeros_like(ref).permute(perm3).contiguous().permute(perm3)
                    )
                    yield b1, b2, ref, out_tensor
            # broadcasting tensors
            for s1, s2, s3, s4, s5, s6 in itertools.product((True, False), repeat=6):
                shape1 = (num_batches if s1 else 1, M if s2 else 1, N if s3 else 1)
                shape2 = (num_batches if s4 else 1, N if s5 else 1, O if s6 else 1)
                b1 = (
                    make_tensor(
                        shape1, dtype=dtype, device=device, low=-1, high=1
                    ).expand(num_batches, M, N)
                    * 0.1
                )
                b2 = (
                    make_tensor(
                        shape2, dtype=dtype, device=device, low=-1, high=1
                    ).expand(num_batches, N, O)
                    * 0.1
                )
                ref = (
                    torch.from_numpy(
                        b1.to(numpy_dtype).cpu().numpy()
                        @ b2.to(numpy_dtype).cpu().numpy()
                    )
                    .to(device=device, dtype=dtype)
                    .sum(0)
                )
                out_tensor = torch.zeros_like(ref)
                yield b1, b2, ref, out_tensor
            # zero-sized tensors
            for z1, z2, z3, z4 in itertools.product((True, False), repeat=4):
                shape1 = (num_batches if z1 else 0, M if z2 else 0, N if z3 else 0)
                shape2 = (num_batches if z1 else 0, N if z3 else 0, O if z4 else 0)
                b1 = (
                    make_tensor(shape1, dtype=dtype, device=device, low=-1, high=1)
                    * 0.1
                )
                b2 = (
                    make_tensor(shape2, dtype=dtype, device=device, low=-1, high=1)
                    * 0.1
                )
                ref = (
                    torch.from_numpy(
                        b1.to(numpy_dtype).cpu().numpy()
                        @ b2.to(numpy_dtype).cpu().numpy()
                    )
                    .to(device=device, dtype=dtype)
                    .sum(0)
                )
                out_tensor = torch.zeros_like(ref)
                yield b1, b2, ref, out_tensor