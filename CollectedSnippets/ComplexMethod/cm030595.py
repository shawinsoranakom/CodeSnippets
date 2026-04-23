def check_blake2(self, constructor, salt_size, person_size, key_size,
                     digest_size, max_offset):
        self.assertEqual(constructor.SALT_SIZE, salt_size)
        for i in range(salt_size + 1):
            constructor(salt=b'a' * i)
        salt = b'a' * (salt_size + 1)
        self.assertRaises(ValueError, constructor, salt=salt)

        self.assertEqual(constructor.PERSON_SIZE, person_size)
        for i in range(person_size+1):
            constructor(person=b'a' * i)
        person = b'a' * (person_size + 1)
        self.assertRaises(ValueError, constructor, person=person)

        self.assertEqual(constructor.MAX_DIGEST_SIZE, digest_size)
        for i in range(1, digest_size + 1):
            constructor(digest_size=i)
        self.assertRaises(ValueError, constructor, digest_size=-1)
        self.assertRaises(ValueError, constructor, digest_size=0)
        self.assertRaises(ValueError, constructor, digest_size=digest_size+1)

        self.assertEqual(constructor.MAX_KEY_SIZE, key_size)
        for i in range(key_size+1):
            constructor(key=b'a' * i)
        key = b'a' * (key_size + 1)
        self.assertRaises(ValueError, constructor, key=key)
        self.assertEqual(constructor().hexdigest(),
                         constructor(key=b'').hexdigest())

        for i in range(0, 256):
            constructor(fanout=i)
        self.assertRaises(ValueError, constructor, fanout=-1)
        self.assertRaises(ValueError, constructor, fanout=256)

        for i in range(1, 256):
            constructor(depth=i)
        self.assertRaises(ValueError, constructor, depth=-1)
        self.assertRaises(ValueError, constructor, depth=0)
        self.assertRaises(ValueError, constructor, depth=256)

        for i in range(0, 256):
            constructor(node_depth=i)
        self.assertRaises(ValueError, constructor, node_depth=-1)
        self.assertRaises(ValueError, constructor, node_depth=256)

        for i in range(0, digest_size + 1):
            constructor(inner_size=i)
        self.assertRaises(ValueError, constructor, inner_size=-1)
        self.assertRaises(ValueError, constructor, inner_size=digest_size+1)

        constructor(leaf_size=0)
        constructor(leaf_size=(1<<32)-1)
        self.assertRaises(ValueError, constructor, leaf_size=-1)
        self.assertRaises(OverflowError, constructor, leaf_size=1<<32)

        constructor(node_offset=0)
        constructor(node_offset=max_offset)
        self.assertRaises(ValueError, constructor, node_offset=-1)
        self.assertRaises(OverflowError, constructor, node_offset=max_offset+1)

        self.assertRaises(TypeError, constructor, '')

        constructor(
            b'',
            key=b'',
            salt=b'',
            person=b'',
            digest_size=17,
            fanout=1,
            depth=1,
            leaf_size=256,
            node_offset=512,
            node_depth=1,
            inner_size=7,
            last_node=True
        )