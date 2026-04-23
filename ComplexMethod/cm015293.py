def test_qnnpack_add(self, A, zero_point, scale_A, scale_B, scale_C):
        with override_quantized_engine('qnnpack'):
            A_temp = A
            for channels_last in [True, False]:
                if channels_last and len(A_temp[0].shape) != 4:
                    continue
                A, (scale_a, zero_point_A, torch_type) = A_temp
                B, (scale_b, zero_point_B, torch_type) = A_temp
                A = torch.from_numpy(A)
                B = torch.from_numpy(B)

                if torch_type == torch.qint8 and not torch.backends.xnnpack.enabled:
                    continue

                if channels_last:
                    A = A.to(memory_format=torch.channels_last)
                    B = B.to(memory_format=torch.channels_last)
                assume(scale_A // scale_C >= 2**-14)
                assume(scale_A // scale_C < 2**8)
                assume(scale_B // scale_C >= 2**-14)
                assume(scale_B // scale_C < 2**8)

                zero_point_C = 127
                np_dtype = np.uint8

                if torch_type == torch.qint8:
                    zero_point_C = 0
                    np_dtype = np.int8

                qA = torch.quantize_per_tensor(A, scale=scale_A, zero_point=zero_point,
                                               dtype=torch_type)
                qB = torch.quantize_per_tensor(B, scale=scale_B, zero_point=zero_point,
                                               dtype=torch_type)

                # Add ground truth
                C = (qA.dequantize() + qB.dequantize()).numpy()

                qC = _quantize(C, scale_C, zero_point_C, dtype=np_dtype)

                qC_qnnp = torch.ops.quantized.add(qA, qB, scale_C, zero_point_C)

                np.testing.assert_equal(qC, qC_qnnp.int_repr(),
                                        "Quantized addition failed.")

                Crelu = C.copy()
                Crelu[C < 0] = 0
                qCrelu = torch.quantize_per_tensor(torch.from_numpy(Crelu), scale_C,
                                                   zero_point_C, dtype=torch_type)
                qCrelu_hat = torch.ops.quantized.add_relu(qA, qB, scale=scale_C, zero_point=zero_point_C)
                np.testing.assert_equal(qCrelu.int_repr().numpy(), qCrelu_hat.int_repr(),
                                        "Quantized addition with ReLU failed.")

        """Tests the correctness of the quantized::add (qnnpack) mul."""