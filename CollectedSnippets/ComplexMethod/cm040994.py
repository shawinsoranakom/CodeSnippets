def create_queue(
        self,
        context: RequestContext,
        queue_name: String,
        attributes: QueueAttributeMap = None,
        tags: TagMap = None,
        **kwargs,
    ) -> CreateQueueResult:
        fifo = attributes and (
            attributes.get(QueueAttributeName.FifoQueue, "false").lower() == "true"
        )

        # Special Case TODO: why is an emtpy policy passed at all? same in set_queue_attributes
        if attributes and attributes.get(QueueAttributeName.Policy) == "":
            del attributes[QueueAttributeName.Policy]

        store = self.get_store(context.account_id, context.region)

        with _STORE_LOCK:
            if queue_name in store.queues:
                queue = store.queues[queue_name]

                if attributes:
                    # if attributes are set, then we check whether the existing attributes match the passed ones
                    queue.validate_queue_attributes(attributes)
                    for k, v in attributes.items():
                        if queue.attributes.get(k) != v:
                            LOG.debug(
                                "queue attribute values %s for queue %s do not match %s (existing) != %s (new)",
                                k,
                                queue_name,
                                queue.attributes.get(k),
                                v,
                            )
                            raise QueueNameExists(
                                f"A queue already exists with the same name and a different value for attribute {k}"
                            )

                return CreateQueueResult(QueueUrl=queue.url(context))

            if config.SQS_DELAY_RECENTLY_DELETED:
                deleted = store.deleted.get(queue_name)
                if deleted and deleted > (time.time() - sqs_constants.RECENTLY_DELETED_TIMEOUT):
                    raise QueueDeletedRecently(
                        "You must wait 60 seconds after deleting a queue before you can create "
                        "another with the same name."
                    )
            store.expire_deleted()

            # create the appropriate queue
            if fifo:
                queue = FifoQueue(queue_name, context.region, context.account_id, attributes, tags)
            else:
                queue = StandardQueue(
                    queue_name, context.region, context.account_id, attributes, tags
                )
            if tags:
                self._tag_queue(queue, tags)

            LOG.debug("creating queue key=%s attributes=%s tags=%s", queue_name, attributes, tags)

            store.queues[queue_name] = queue

        return CreateQueueResult(QueueUrl=queue.url(context))