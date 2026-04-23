def test_create_copy_with_inherited_m2m(self):
        restaurant = Restaurant.objects.create()
        supplier = CustomSupplier.objects.create(
            name="Central market", address="944 W. Fullerton"
        )
        supplier.customers.set([restaurant])
        old_customers = supplier.customers.all()
        supplier.pk = None
        supplier.id = None
        supplier._state.adding = True
        supplier.save()
        supplier.customers.set(old_customers)
        supplier = Supplier.objects.get(pk=supplier.pk)
        self.assertCountEqual(supplier.customers.all(), old_customers)
        self.assertSequenceEqual(supplier.customers.all(), [restaurant])