def setUp(self):
        super().setUp()
        self.calib_data = [[torch.rand(2, 5, dtype=torch.float)] for _ in range(2)]
        self.train_data = [
            [
                torch.rand(2, 5, dtype=torch.float),
                torch.randint(0, 1, (2,), dtype=torch.long),
            ]
            for _ in range(2)
        ]
        self.img_data_1d = [[torch.rand(2, 3, 10, dtype=torch.float)] for _ in range(2)]
        self.img_data_2d = [
            [torch.rand(1, 3, 10, 10, dtype=torch.float)] for _ in range(2)
        ]
        self.img_data_3d = [
            [torch.rand(1, 3, 5, 5, 5, dtype=torch.float)] for _ in range(2)
        ]
        self.img_data_1d_train = [
            [
                torch.rand(2, 3, 10, dtype=torch.float),
                torch.randint(0, 1, (1,), dtype=torch.long),
            ]
            for _ in range(2)
        ]
        self.img_data_2d_train = [
            [
                torch.rand(1, 3, 10, 10, dtype=torch.float),
                torch.randint(0, 1, (1,), dtype=torch.long),
            ]
            for _ in range(2)
        ]
        self.img_data_3d_train = [
            [
                torch.rand(1, 3, 5, 5, 5, dtype=torch.float),
                torch.randint(0, 1, (1,), dtype=torch.long),
            ]
            for _ in range(2)
        ]

        self.img_data_dict = {
            1: self.img_data_1d,
            2: self.img_data_2d,
            3: self.img_data_3d,
        }

        # Quant types that produce statically quantized ops
        self.static_quant_types = [QuantType.STATIC, QuantType.QAT]
        # All quant types for (fx based) graph mode quantization
        self.all_quant_types = [QuantType.DYNAMIC, QuantType.STATIC, QuantType.QAT]