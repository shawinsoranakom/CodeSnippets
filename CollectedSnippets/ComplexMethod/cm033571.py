def test_library_with_no_crypt_r_or_crypt_gensalt_rn(self, mocker: MockerFixture) -> None:
        """Test that a library without crypt_r() or crypt_gensalt_rn() is prepped correctly."""
        mock_libs = (
            _CryptLib(None),
        )

        class MockCDLL:

            class MockCrypt:
                def __init__(self):
                    self.argtypes = None
                    self.restype = None

            def __init__(self):
                self.crypt = self.MockCrypt()
                self.crypt_gensalt = self.MockCrypt()

        mocker.patch('ansible._internal._encryption._crypt._CRYPT_LIBS', mock_libs)
        mocker.patch('ctypes.cdll.LoadLibrary', return_value=MockCDLL())

        crypt_facade = CryptFacade()

        assert crypt_facade._crypt_impl is not None
        assert crypt_facade._crypt_impl.argtypes is not None
        assert crypt_facade._crypt_impl.restype is not None
        assert crypt_facade._use_crypt_r is False

        assert crypt_facade._crypt_gensalt_impl is not None
        assert crypt_facade._crypt_gensalt_impl.argtypes is not None
        assert crypt_facade._crypt_gensalt_impl.restype is not None
        assert crypt_facade._use_crypt_gensalt_rn is False
        assert crypt_facade.has_crypt_gensalt