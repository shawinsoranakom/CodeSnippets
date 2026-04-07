def on_commit():
            with transaction.atomic():
                t = Thing.objects.create(num=1)
                self.notify(t.num)