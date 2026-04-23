def state_task_service_for(service_name: str) -> StateTaskService:
    match service_name:
        case "aws-sdk":
            return StateTaskServiceAwsSdk()
        case "lambda":
            return StateTaskServiceLambda()
        case "sqs":
            return StateTaskServiceSqs()
        case "states":
            return StateTaskServiceSfn()
        case "dynamodb":
            return StateTaskServiceDynamoDB()
        case "apigateway":
            return StateTaskServiceApiGateway()
        case "sns":
            return StateTaskServiceSns()
        case "events":
            return StateTaskServiceEvents()
        case "ecs":
            return StateTaskServiceEcs()
        case "glue":
            return StateTaskServiceGlue()
        case "batch":
            return StateTaskServiceBatch()
        case _ if service_name in _UNSUPPORTED_SERVICE_NAMES:
            return StateTaskServiceUnsupported()
        case unknown:
            raise RecognitionException(f"Unknown service '{unknown}'")