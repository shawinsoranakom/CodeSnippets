def test_model_inheritance(self):
        # Regression for #7350, #7202
        # When you create a Parent object with a specific reference to an
        # existent child instance, saving the Parent doesn't duplicate the
        # child. This behavior is only activated during a raw save - it is
        # mostly relevant to deserialization, but any sort of CORBA style
        # 'narrow()' API would require a similar approach.

        # Create a child-parent-grandparent chain
        place1 = Place(name="Guido's House of Pasta", address="944 W. Fullerton")
        place1.save_base(raw=True)
        restaurant = Restaurant(
            place_ptr=place1,
            serves_hot_dogs=True,
            serves_pizza=False,
        )
        restaurant.save_base(raw=True)
        italian_restaurant = ItalianRestaurant(
            restaurant_ptr=restaurant, serves_gnocchi=True
        )
        italian_restaurant.save_base(raw=True)

        # Create a child-parent chain with an explicit parent link
        place2 = Place(name="Main St", address="111 Main St")
        place2.save_base(raw=True)
        park = ParkingLot(parent=place2, capacity=100)
        park.save_base(raw=True)

        # No extra parent objects have been created.
        places = list(Place.objects.all())
        self.assertEqual(places, [place1, place2])

        dicts = list(Restaurant.objects.values("name", "serves_hot_dogs"))
        self.assertEqual(
            dicts, [{"name": "Guido's House of Pasta", "serves_hot_dogs": True}]
        )

        dicts = list(
            ItalianRestaurant.objects.values(
                "name", "serves_hot_dogs", "serves_gnocchi"
            )
        )
        self.assertEqual(
            dicts,
            [
                {
                    "name": "Guido's House of Pasta",
                    "serves_gnocchi": True,
                    "serves_hot_dogs": True,
                }
            ],
        )

        dicts = list(ParkingLot.objects.values("name", "capacity"))
        self.assertEqual(
            dicts,
            [
                {
                    "capacity": 100,
                    "name": "Main St",
                }
            ],
        )

        # You can also update objects when using a raw save.
        place1.name = "Guido's All New House of Pasta"
        place1.save_base(raw=True)

        restaurant.serves_hot_dogs = False
        restaurant.save_base(raw=True)

        italian_restaurant.serves_gnocchi = False
        italian_restaurant.save_base(raw=True)

        place2.name = "Derelict lot"
        place2.save_base(raw=True)

        park.capacity = 50
        park.save_base(raw=True)

        # No extra parent objects after an update, either.
        places = list(Place.objects.all())
        self.assertEqual(places, [place2, place1])
        self.assertEqual(places[0].name, "Derelict lot")
        self.assertEqual(places[1].name, "Guido's All New House of Pasta")

        dicts = list(Restaurant.objects.values("name", "serves_hot_dogs"))
        self.assertEqual(
            dicts,
            [
                {
                    "name": "Guido's All New House of Pasta",
                    "serves_hot_dogs": False,
                }
            ],
        )

        dicts = list(
            ItalianRestaurant.objects.values(
                "name", "serves_hot_dogs", "serves_gnocchi"
            )
        )
        self.assertEqual(
            dicts,
            [
                {
                    "name": "Guido's All New House of Pasta",
                    "serves_gnocchi": False,
                    "serves_hot_dogs": False,
                }
            ],
        )

        dicts = list(ParkingLot.objects.values("name", "capacity"))
        self.assertEqual(
            dicts,
            [
                {
                    "capacity": 50,
                    "name": "Derelict lot",
                }
            ],
        )

        # If you try to raw_save a parent attribute onto a child object,
        # the attribute will be ignored.

        italian_restaurant.name = "Lorenzo's Pasta Hut"
        italian_restaurant.save_base(raw=True)

        # Note that the name has not changed
        # - name is an attribute of Place, not ItalianRestaurant
        dicts = list(
            ItalianRestaurant.objects.values(
                "name", "serves_hot_dogs", "serves_gnocchi"
            )
        )
        self.assertEqual(
            dicts,
            [
                {
                    "name": "Guido's All New House of Pasta",
                    "serves_gnocchi": False,
                    "serves_hot_dogs": False,
                }
            ],
        )