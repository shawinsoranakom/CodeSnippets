def test_can_parse_bsd_format(self):
        """Test detection of BSD checksum format."""
        parser = BSDFormat()

        # Valid BSD formats
        assert parser.can_parse("MD5 (file.txt) = d41d8cd98f00b204e9800998ecf8427e")
        assert parser.can_parse(
            "SHA256 (test.zip) = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        assert parser.can_parse(
            "SHA512 (binary.exe) = cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        )
        assert parser.can_parse("SHA1 (test) = da39a3ee5e6b4b0d3255bfef95601890afd80709")

        # With spaces
        assert parser.can_parse(
            "SHA256 (file with spaces.txt) = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

        # Invalid formats
        assert not parser.can_parse("d41d8cd98f00b204e9800998ecf8427e  file.txt")
        assert not parser.can_parse("file.txt: d41d8cd98f00b204e9800998ecf8427e")
        assert not parser.can_parse(
            "SHA3 (file.txt) = d41d8cd98f00b204e9800998ecf8427e"
        )