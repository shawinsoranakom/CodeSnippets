def test_storage_error(self):
        quantized_storages = [
            torch.QInt32Storage,
            torch.QInt8Storage,
            torch.QUInt2x4Storage,
            torch.QUInt4x2Storage,
            torch.QUInt8Storage,
        ]

        with self.assertRaisesRegex(RuntimeError, r"Only child classes of _LegacyStorage can be instantiated"):
            torch.storage._LegacyStorage()

        for storage_class in torch._storage_classes:
            if storage_class in [torch.UntypedStorage, torch.TypedStorage]:
                continue

            device = 'cuda' if storage_class.__module__ == 'torch.cuda' else 'cpu'
            dtype = storage_class.dtype

            if device == 'cuda' and not torch.cuda.is_available():
                continue

            # Legacy <type>Storage constructor errors
            with self.assertRaisesRegex(RuntimeError, r"'device' cannot be specified"):
                storage_class(device='cpu')

            with self.assertRaisesRegex(RuntimeError, r"'dtype' cannot be specified"):
                storage_class(dtype=torch.float)

            with self.assertRaisesRegex(TypeError, r"got an unexpected keyword"):
                storage_class(sdlkjf=torch.float)

            with self.assertRaisesRegex(RuntimeError, r"Too many positional arguments"):
                storage_class(0, 0)

            with self.assertRaisesRegex(TypeError, r"invalid data type"):
                storage_class('string')

            with self.assertRaisesRegex(TypeError, r"Argument type not recognized"):
                storage_class(torch.tensor([]))

            s = storage_class()

            with self.assertRaisesRegex(RuntimeError, r"No positional arguments"):
                storage_class(0, wrap_storage=s.untyped())

            with self.assertRaisesRegex(TypeError, r"must be UntypedStorage"):
                storage_class(wrap_storage=s)

            if torch.cuda.is_available():
                if storage_class in quantized_storages:
                    with self.assertRaisesRegex(RuntimeError, r"Cannot create CUDA storage with quantized dtype"):
                        s.cuda()

                else:

                    if s.is_cuda:
                        s_other_device = s.cpu()
                    else:
                        s_other_device = s.cuda()

                    with self.assertRaisesRegex(RuntimeError, r"Device of 'wrap_storage' must be"):
                        storage_class(wrap_storage=s_other_device.untyped())

            # TypedStorage constructor errors
            with self.assertRaisesRegex(RuntimeError, r"No positional arguments"):
                torch.TypedStorage(0, wrap_storage=s.untyped(), dtype=dtype)

            with self.assertRaisesRegex(RuntimeError, r"Argument 'dtype' must be specified"):
                torch.TypedStorage(wrap_storage=s.untyped())

            with self.assertRaisesRegex(TypeError, r"Argument 'dtype' must be torch.dtype"):
                torch.TypedStorage(wrap_storage=s.untyped(), dtype=0)

            with self.assertRaisesRegex(RuntimeError, r"Argument 'device' should not be specified"):
                torch.TypedStorage(wrap_storage=s.untyped(), dtype=dtype, device=device)

            with self.assertRaisesRegex(TypeError, r"Argument 'wrap_storage' must be UntypedStorage"):
                torch.TypedStorage(wrap_storage=s, dtype=dtype)

            with self.assertRaisesRegex(RuntimeError, r"Storage device not recognized"):
                torch.TypedStorage(dtype=dtype, device='xla')

            if torch.cuda.is_available():
                if storage_class in quantized_storages:
                    with self.assertRaisesRegex(RuntimeError, r"Cannot create CUDA storage with quantized dtype"):
                        torch.TypedStorage(dtype=dtype, device='cuda')

            with self.assertRaisesRegex(TypeError, r"Argument type not recognized"):
                torch.TypedStorage(torch.tensor([]), dtype=dtype, device=device)

            with self.assertRaisesRegex(RuntimeError, r"Too many positional arguments"):
                torch.TypedStorage(0, 0, dtype=dtype, device=device)

            if isinstance(s, torch.TypedStorage):
                s_other = torch.TypedStorage([1, 2, 3, 4], device=device, dtype=dtype)

                with self.assertRaisesRegex(RuntimeError, r'cannot set item'):
                    s.fill_(s_other)