def test_parse_bsd_format(self):
        """Test parsing of BSD checksum format."""
        parser = BSDFormat()

        content = """
MD5 (file1.txt) = d41d8cd98f00b204e9800998ecf8427e
SHA256 (file2.zip) = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
SHA1 (binary.exe) = da39a3ee5e6b4b0d3255bfef95601890afd80709
SHA512 (large.bin) = cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e
SHA256 (file with (parentheses).txt) = 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
MD5 (UPPERCASE.TXT) = ABCDEF1234567890ABCDEF1234567890
        """

        result = parser.parse(content)

        assert len(result) == 6
        assert result["file1.txt"] == "d41d8cd98f00b204e9800998ecf8427e"
        assert (
            result["file2.zip"]
            == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        assert result["binary.exe"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        assert (
            result["large.bin"]
            == "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        )
        assert (
            result["file with (parentheses).txt"]
            == "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )
        assert result["UPPERCASE.TXT"] == "abcdef1234567890abcdef1234567890"