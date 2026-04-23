def test_save_as_new_with_new_inlines(self):
        """
        Existing and new inlines are saved with save_as_new.

        Regression for #14938.
        """
        efnet = Network.objects.create(name="EFNet")
        host1 = Host.objects.create(hostname="irc.he.net", network=efnet)

        HostFormSet = inlineformset_factory(Network, Host, fields="__all__")

        # Add a new host, modify previous host, and save-as-new
        data = {
            "host_set-TOTAL_FORMS": "2",
            "host_set-INITIAL_FORMS": "1",
            "host_set-MAX_NUM_FORMS": "0",
            "host_set-0-id": str(host1.id),
            "host_set-0-hostname": "tranquility.hub.dal.net",
            "host_set-1-hostname": "matrix.de.eu.dal.net",
        }

        # To save a formset as new, it needs a new hub instance
        dalnet = Network.objects.create(name="DALnet")
        formset = HostFormSet(data, instance=dalnet, save_as_new=True)

        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertQuerySetEqual(
            dalnet.host_set.order_by("hostname"),
            Host.objects.filter(
                hostname__in=[
                    "matrix.de.eu.dal.net",
                    "tranquility.hub.dal.net",
                ]
            ).order_by("hostname"),
        )