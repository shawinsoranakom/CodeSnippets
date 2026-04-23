def test_io(self, io_type, io_data1, io_data2, io_data3):
        io1 = io_type(io_data1)
        io2 = io_type(io_data2)
        io3 = io_type(io_data3)

        self.assertEqual(get_hash(io1), get_hash(io3))
        self.assertNotEqual(get_hash(io1), get_hash(io2))

        # Changing the stream position should change the hash
        io1.seek(1)
        io3.seek(0)
        self.assertNotEqual(get_hash(io1), get_hash(io3))