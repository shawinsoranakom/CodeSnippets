def check_statx_attributes(self, filename):
        maximal_mask = 0
        for name in dir(os):
            if name.startswith('STATX_'):
                maximal_mask |= getattr(os, name)
        result = os.statx(filename, maximal_mask)
        stat_result = os.stat(filename)

        time_attributes = ('stx_atime', 'stx_btime', 'stx_ctime', 'stx_mtime')
        # gh-83714: stx_btime can be None on tmpfs even if STATX_BTIME mask
        # is used
        time_attributes = [name for name in time_attributes
                           if getattr(result, name) is not None]
        self.check_timestamp_agreement(result, time_attributes)

        def getmask(name):
            return getattr(os, name, 0)

        requirements = (
            ('stx_atime', os.STATX_ATIME),
            ('stx_atime_ns', os.STATX_ATIME),
            ('stx_atomic_write_segments_max', getmask('STATX_WRITE_ATOMIC')),
            ('stx_atomic_write_unit_max', getmask('STATX_WRITE_ATOMIC')),
            ('stx_atomic_write_unit_max_opt', getmask('STATX_WRITE_ATOMIC')),
            ('stx_atomic_write_unit_min', getmask('STATX_WRITE_ATOMIC')),
            ('stx_attributes', 0),
            ('stx_attributes_mask', 0),
            ('stx_blksize', 0),
            ('stx_blocks', os.STATX_BLOCKS),
            ('stx_btime', os.STATX_BTIME),
            ('stx_btime_ns', os.STATX_BTIME),
            ('stx_ctime', os.STATX_CTIME),
            ('stx_ctime_ns', os.STATX_CTIME),
            ('stx_dev', 0),
            ('stx_dev_major', 0),
            ('stx_dev_minor', 0),
            ('stx_dio_mem_align', getmask('STATX_DIOALIGN')),
            ('stx_dio_offset_align', getmask('STATX_DIOALIGN')),
            ('stx_dio_read_offset_align', getmask('STATX_DIO_READ_ALIGN')),
            ('stx_gid', os.STATX_GID),
            ('stx_ino', os.STATX_INO),
            ('stx_mask', 0),
            ('stx_mnt_id', getmask('STATX_MNT_ID')),
            ('stx_mode', os.STATX_TYPE | os.STATX_MODE),
            ('stx_mtime', os.STATX_MTIME),
            ('stx_mtime_ns', os.STATX_MTIME),
            ('stx_nlink', os.STATX_NLINK),
            ('stx_rdev', 0),
            ('stx_rdev_major', 0),
            ('stx_rdev_minor', 0),
            ('stx_size', os.STATX_SIZE),
            ('stx_subvol', getmask('STATX_SUBVOL')),
            ('stx_uid', os.STATX_UID),
        )
        optional_members = {
            'stx_atomic_write_segments_max',
            'stx_atomic_write_unit_max',
            'stx_atomic_write_unit_max_opt',
            'stx_atomic_write_unit_min',
            'stx_dio_mem_align',
            'stx_dio_offset_align',
            'stx_dio_read_offset_align',
            'stx_mnt_id',
            'stx_subvol',
        }
        float_type = {
            'stx_atime',
            'stx_btime',
            'stx_ctime',
            'stx_mtime',
        }

        members = set(name for name in dir(result)
                      if name.startswith('stx_'))
        tested = set(name for name, mask in requirements)
        if members - tested:
            raise ValueError(f"statx members not tested: {members - tested}")

        for name, mask in requirements:
            with self.subTest(name=name):
                try:
                    x = getattr(result, name)
                except AttributeError:
                    if name in optional_members:
                        continue
                    else:
                        raise

                if not(result.stx_mask & mask == mask):
                    self.assertIsNone(x)
                    continue

                if name in float_type:
                    self.assertIsInstance(x, float)
                else:
                    self.assertIsInstance(x, int)

                # Compare with stat_result
                try:
                    b = getattr(stat_result, "st_" + name[4:])
                except AttributeError:
                    pass
                else:
                    self.assertEqual(type(x), type(b))
                    if isinstance(x, float):
                        self.assertAlmostEqual(x, b)
                    else:
                        self.assertEqual(x, b)

        self.assertEqual(result.stx_rdev_major, os.major(result.stx_rdev))
        self.assertEqual(result.stx_rdev_minor, os.minor(result.stx_rdev))
        self.assertEqual(result.stx_dev_major, os.major(result.stx_dev))
        self.assertEqual(result.stx_dev_minor, os.minor(result.stx_dev))

        self.assertEqual(result.stx_attributes & result.stx_attributes_mask,
                         result.stx_attributes)