def test_pytorch_model(self):
        a = torchvision.models.resnet.resnet18()
        b = torchvision.models.resnet.resnet18()

        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))