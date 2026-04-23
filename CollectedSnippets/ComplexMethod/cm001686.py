def image_face_points(im, settings):
    if settings.dnn_model_path is not None:
        detector = cv2.FaceDetectorYN.create(
            settings.dnn_model_path,
            "",
            (im.width, im.height),
            0.9,  # score threshold
            0.3,  # nms threshold
            5000  # keep top k before nms
        )
        faces = detector.detect(np.array(im))
        results = []
        if faces[1] is not None:
            for face in faces[1]:
                x = face[0]
                y = face[1]
                w = face[2]
                h = face[3]
                results.append(
                    PointOfInterest(
                        int(x + (w * 0.5)),  # face focus left/right is center
                        int(y + (h * 0.33)),  # face focus up/down is close to the top of the head
                        size=w,
                        weight=1 / len(faces[1])
                    )
                )
        return results
    else:
        np_im = np.array(im)
        gray = cv2.cvtColor(np_im, cv2.COLOR_BGR2GRAY)

        tries = [
            [f'{cv2.data.haarcascades}haarcascade_eye.xml', 0.01],
            [f'{cv2.data.haarcascades}haarcascade_frontalface_default.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_profileface.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_frontalface_alt.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_frontalface_alt2.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_frontalface_alt_tree.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_eye_tree_eyeglasses.xml', 0.05],
            [f'{cv2.data.haarcascades}haarcascade_upperbody.xml', 0.05]
        ]
        for t in tries:
            classifier = cv2.CascadeClassifier(t[0])
            minsize = int(min(im.width, im.height) * t[1])  # at least N percent of the smallest side
            try:
                faces = classifier.detectMultiScale(gray, scaleFactor=1.1,
                                                    minNeighbors=7, minSize=(minsize, minsize),
                                                    flags=cv2.CASCADE_SCALE_IMAGE)
            except Exception:
                continue

            if faces:
                rects = [[f[0], f[1], f[0] + f[2], f[1] + f[3]] for f in faces]
                return [PointOfInterest((r[0] + r[2]) // 2, (r[1] + r[3]) // 2, size=abs(r[0] - r[2]),
                                        weight=1 / len(rects)) for r in rects]
    return []