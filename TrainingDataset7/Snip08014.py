def sync_transaction():
                with transaction.atomic(using=using):
                    obj.save(
                        force_insert=must_create,
                        force_update=not must_create,
                        using=using,
                    )