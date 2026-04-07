def on_commit(i, add_hook):
            with transaction.atomic():
                if add_hook:
                    transaction.on_commit(lambda: on_commit(i + 10, False))
                t = Thing.objects.create(num=i)
                self.notify(t.num)