def test_noncallable_view(self):
        # View is not a callable (explicit import; arbitrary Python object)
        with self.assertRaisesMessage(TypeError, "view must be a callable"):
            path("uncallable-object/", views.uncallable)