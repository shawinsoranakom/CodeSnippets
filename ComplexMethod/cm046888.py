def fix_message_factory_issue():
    try:
        import google.protobuf.message_factory

        class MessageFactory:
            def CreatePrototype(self, *args, **kwargs):
                return

            def GetMessages(self, *args, **kwargs):
                return

            def GetPrototype(self, *args, **kwargs):
                return

        if not hasattr(google.protobuf.message_factory, "MessageFactory"):
            logger.info("Unsloth: Patching protobuf.MessageFactory as it doesn't exist")
            google.protobuf.message_factory.MessageFactory = MessageFactory
        elif (
            hasattr(google.protobuf.message_factory, "MessageFactory")
            and not hasattr(
                google.protobuf.message_factory.MessageFactory, "GetPrototype"
            )
            and not hasattr(google.protobuf.message_factory, "GetMessageClass")
        ):
            google.protobuf.message_factory.MessageFactory = MessageFactory
            logger.info("Unsloth: Patching protobuf.MessageFactory as it doesn't exist")
        elif (
            hasattr(google.protobuf.message_factory, "MessageFactory")
            and not hasattr(
                google.protobuf.message_factory.MessageFactory, "GetPrototype"
            )
            and hasattr(google.protobuf.message_factory, "GetMessageClass")
        ):
            GetMessageClass = google.protobuf.message_factory.GetMessageClass

            def GetPrototype(self, descriptor):
                return GetMessageClass(descriptor)

            google.protobuf.message_factory.MessageFactory.GetPrototype = GetPrototype
            logger.info("Unsloth: Patching protobuf.MessageFactory.GetPrototype")
        pass
    except:
        pass