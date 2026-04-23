def test_fk_assignment_and_related_object_cache(self):
        # Tests of ForeignKey assignment and the related-object cache (see
        # #6886).

        p = Parent.objects.create(name="Parent")
        c = Child.objects.create(name="Child", parent=p)

        # Look up the object again so that we get a "fresh" object.
        c = Child.objects.get(name="Child")
        p = c.parent

        # Accessing the related object again returns the exactly same object.
        self.assertIs(c.parent, p)

        # But if we kill the cache, we get a new object.
        del c._state.fields_cache["parent"]
        self.assertIsNot(c.parent, p)

        # Assigning a new object results in that object getting cached
        # immediately.
        p2 = Parent.objects.create(name="Parent 2")
        c.parent = p2
        self.assertIs(c.parent, p2)

        # Assigning None succeeds if field is null=True.
        p.bestchild = None
        self.assertIsNone(p.bestchild)

        # bestchild should still be None after saving.
        p.save()
        self.assertIsNone(p.bestchild)

        # bestchild should still be None after fetching the object again.
        p = Parent.objects.get(name="Parent")
        self.assertIsNone(p.bestchild)

        # Assigning None will not fail: Child.parent is null=False.
        setattr(c, "parent", None)

        # You also can't assign an object of the wrong type here
        msg = (
            'Cannot assign "<First: First object (1)>": "Child.parent" must '
            'be a "Parent" instance.'
        )
        with self.assertRaisesMessage(ValueError, msg):
            setattr(c, "parent", First(id=1, second=1))

        # You can assign None to Child.parent during object creation.
        Child(name="xyzzy", parent=None)

        # But when trying to save a Child with parent=None, the database will
        # raise IntegrityError.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Child.objects.create(name="xyzzy", parent=None)

        # Creation using keyword argument should cache the related object.
        p = Parent.objects.get(name="Parent")
        c = Child(parent=p)
        self.assertIs(c.parent, p)

        # Creation using keyword argument and unsaved related instance (#8070).
        p = Parent()
        msg = (
            "save() prohibited to prevent data loss due to unsaved related object "
            "'parent'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Child.objects.create(parent=p)

        with self.assertRaisesMessage(ValueError, msg):
            ToFieldChild.objects.create(parent=p)

        # Creation using attname keyword argument and an id will cause the
        # related object to be fetched.
        p = Parent.objects.get(name="Parent")
        c = Child(parent_id=p.id)
        self.assertIsNot(c.parent, p)
        self.assertEqual(c.parent, p)