def test_restjson_header_target_serialization():
    """
    Tests the serialization of attributes into a specified header key based on this example from glacier:

        "InitiateJobOutput":{
          "type":"structure",
          "members":{
            "location":{
              "shape":"string",
              "location":"header",
              "locationName":"Location"
            },
            "jobId":{
              "shape":"string",
              "location":"header",
              "locationName":"x-amz-job-id"
            },
            "jobOutputPath":{
              "shape":"string",
              "location":"header",
              "locationName":"x-amz-job-output-path"
            }
          },
          "documentation":"<p>Contains the Amazon S3 Glacier response to your request.</p>"
        },
    """
    response = {
        "location": "/here",
        "jobId": "42069",
        "jobOutputPath": "/there",
    }

    result = _botocore_serializer_integration_test(
        service="glacier",
        action="InitiateJob",
        response=response,
        status_code=202,
    )

    headers = result["ResponseMetadata"]["HTTPHeaders"]
    assert "location" in headers
    assert "x-amz-job-id" in headers
    assert "x-amz-job-output-path" in headers
    assert "locationName" not in headers
    assert "jobOutputPath" not in headers

    assert headers["location"] == "/here"
    assert headers["x-amz-job-id"] == "42069"
    assert headers["x-amz-job-output-path"] == "/there"