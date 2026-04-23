def test_cosine_embedding_loss_with_diff_type(self):
        for device in device_():
            input1 = torch.tensor([[2, 3, 4], [6, 2, 4]], dtype=torch.double, device=device)
            input2 = torch.tensor([[2, 3, 5], [3, 2, 1]], dtype=torch.double, device=device)
            target = torch.tensor([1, -1], dtype=torch.int, device=device)
            expected = torch.nn.functional.cosine_embedding_loss(input1, input2, target)
            for dt1 in get_all_math_dtypes(device):
                for dt2 in get_all_math_dtypes(device):
                    for dt3 in get_all_math_dtypes(device):
                        # dt3 is used as dtype for target = [1, -1], so let's skip unsigned type
                        if dt3 == torch.uint8:
                            continue
                        if dt1.is_complex or dt2.is_complex or dt3.is_complex:
                            continue
                        input1 = input1.to(dt1)
                        input2 = input2.to(dt2)
                        target = target.to(dt3)
                        result = torch.nn.functional.cosine_embedding_loss(input1, input2, target)
                        self.assertEqual(result.item(), expected.item(), atol=0.001, rtol=0)