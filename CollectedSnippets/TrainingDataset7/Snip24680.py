def test_destructor_catches_importerror(self):
        class FakeGeom(CPointerBase):
            destructor = mock.Mock(side_effect=ImportError)

        fg = FakeGeom()
        fg.ptr = fg.ptr_type(1)
        del fg