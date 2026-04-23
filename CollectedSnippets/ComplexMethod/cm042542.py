def test_isinstance(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ScrapyDeprecationWarning)
            DeprecatedName = create_deprecated_class("DeprecatedName", NewName)

            class UpdatedUserClass2(NewName):
                pass

            class UpdatedUserClass2a(NewName):
                pass

            class OutdatedUserClass2(DeprecatedName):
                pass

            class OutdatedUserClass2a(DeprecatedName):
                pass

            class UnrelatedClass:
                pass

        assert isinstance(UpdatedUserClass2(), NewName)
        assert isinstance(UpdatedUserClass2a(), NewName)
        assert isinstance(UpdatedUserClass2(), DeprecatedName)
        assert isinstance(UpdatedUserClass2a(), DeprecatedName)
        assert isinstance(OutdatedUserClass2(), DeprecatedName)
        assert isinstance(OutdatedUserClass2a(), DeprecatedName)
        assert not isinstance(OutdatedUserClass2a(), OutdatedUserClass2)
        assert not isinstance(OutdatedUserClass2(), OutdatedUserClass2a)
        assert not isinstance(UnrelatedClass(), DeprecatedName)