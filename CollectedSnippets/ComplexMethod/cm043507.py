def main():
    closed_count = 0
    video_capture = cv2.VideoCapture(0)

    ret, frame = video_capture.read(0)
    # cv2.VideoCapture.release()
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)
    process = True

    while True:
        ret, frame = video_capture.read(0)

        # get it into the correct format
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]



        # get the correct face landmarks

        if process:
            face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)

            # get eyes
            for face_landmark in face_landmarks_list:
                left_eye = face_landmark['left_eye']
                right_eye = face_landmark['right_eye']


                color = (255,0,0)
                thickness = 2

                cv2.rectangle(small_frame, left_eye[0], right_eye[-1], color, thickness)

                cv2.imshow('Video', small_frame)

                ear_left = get_ear(left_eye)
                ear_right = get_ear(right_eye)

                closed = ear_left < 0.2 and ear_right < 0.2

                if (closed):
                    closed_count += 1

                else:
                    closed_count = 0

                if (closed_count >= EYES_CLOSED_SECONDS):
                    asleep = True
                    while (asleep): #continue this loop until they wake up and acknowledge music
                        print("EYES CLOSED")

                        if cv2.waitKey(1) == 32: #Wait for space key  
                            asleep = False
                            print("EYES OPENED")
                    closed_count = 0

        process = not process
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break