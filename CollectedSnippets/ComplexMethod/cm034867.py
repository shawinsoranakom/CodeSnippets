def test_lang_and_ocr_version():
    ocr_engine = PaddleOCR(lang="ch", ocr_version="PP-OCRv5")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv5_server_det"
    assert ocr_engine._params["text_recognition_model_name"] == "PP-OCRv5_server_rec"
    ocr_engine = PaddleOCR(lang="chinese_cht", ocr_version="PP-OCRv5")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv5_server_det"
    assert ocr_engine._params["text_recognition_model_name"] == "PP-OCRv5_server_rec"
    ocr_engine = PaddleOCR(lang="en", ocr_version="PP-OCRv5")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv5_server_det"
    assert ocr_engine._params["text_recognition_model_name"] == "en_PP-OCRv5_mobile_rec"
    ocr_engine = PaddleOCR(lang="japan", ocr_version="PP-OCRv5")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv5_server_det"
    assert ocr_engine._params["text_recognition_model_name"] == "PP-OCRv5_server_rec"
    ocr_engine = PaddleOCR(lang="ch", ocr_version="PP-OCRv4")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv4_mobile_det"
    assert ocr_engine._params["text_recognition_model_name"] == "PP-OCRv4_mobile_rec"
    ocr_engine = PaddleOCR(lang="en", ocr_version="PP-OCRv4")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv4_mobile_det"
    assert ocr_engine._params["text_recognition_model_name"] == "en_PP-OCRv4_mobile_rec"
    ocr_engine = PaddleOCR(lang="ch", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert ocr_engine._params["text_recognition_model_name"] == "PP-OCRv3_mobile_rec"
    ocr_engine = PaddleOCR(lang="en", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert ocr_engine._params["text_recognition_model_name"] == "en_PP-OCRv3_mobile_rec"
    ocr_engine = PaddleOCR(lang="fr", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert (
        ocr_engine._params["text_recognition_model_name"] == "latin_PP-OCRv3_mobile_rec"
    )
    ocr_engine = PaddleOCR(lang="ar", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert (
        ocr_engine._params["text_recognition_model_name"]
        == "arabic_PP-OCRv3_mobile_rec"
    )
    ocr_engine = PaddleOCR(lang="ru", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert (
        ocr_engine._params["text_recognition_model_name"]
        == "cyrillic_PP-OCRv3_mobile_rec"
    )
    ocr_engine = PaddleOCR(lang="hi", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert (
        ocr_engine._params["text_recognition_model_name"]
        == "devanagari_PP-OCRv3_mobile_rec"
    )
    ocr_engine = PaddleOCR(lang="japan", ocr_version="PP-OCRv3")
    assert ocr_engine._params["text_detection_model_name"] == "PP-OCRv3_mobile_det"
    assert (
        ocr_engine._params["text_recognition_model_name"] == "japan_PP-OCRv3_mobile_rec"
    )