#-----Step 1: Use VideoCapture in OpenCV-----
import cv2
import dlib
import math
import os
import time
import numpy as np
import sys
import glob
import serial
# brew install brightness as well

BLINK_RATIO_THRESHOLD = 5.7
VIDEO_LOCATION = "cam_video.mp4"
num_secs = 20

def clear_saved_data():
    mydir = os.getcwd() + "/data"
    filelist = [ f for f in os.listdir(mydir) ]
    for f in filelist:
        os.remove(os.path.join(mydir, f))
    try:
        os.remove(os.path.join(os.getcwd(), VIDEO_LOCATION))
    except:
        return
    finally:
        return

def save_video():
    # This will return video from the first webcam on your computer.
    cap = cv2.VideoCapture(0)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    capture_size = (int(cap.get(3)), int(cap.get(4)))
    out = cv2.VideoWriter(VIDEO_LOCATION, fourcc, 20.0, capture_size)

    start = time.time()
    frameCount = 0
    # loop runs if capturing has been initialized.
    while time.time() - start <= num_secs:
        # reads frames from a camera
        # ret checks return at each frame
        ret, frame = cap.read()
        frameCount += 1

        if ret == False:
            break

        frameCount += 1

        # output the frame
        out.write(frame)

    elapsed_time = time.time() - start

    if elapsed_time < num_secs - 0.9 * num_secs:
        return "Error"

    print()
    print("Sample time:", elapsed_time)
    print("Frames sampled:", frameCount)
    print()
    print("Frames/Sec", frameCount/elapsed_time)

    # Close the window / Release webcam
    cap.release()
    # After we release our webcam, we also release the output
    out.release()
    # De-allocate any associated memory usage
    cv2.destroyAllWindows()

    print()
    print("Saved")

    return "Success"

#-----Step 5: Getting to know blink ratio

def midpoint(point1 ,point2):
    return (point1.x + point2.x)/2,(point1.y + point2.y)/2

def euclidean_distance(point1 , point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_blink_ratio(eye_points, facial_landmarks):

    #loading all the required points
    corner_left  = (facial_landmarks.part(eye_points[0]).x,
                    facial_landmarks.part(eye_points[0]).y)
    corner_right = (facial_landmarks.part(eye_points[3]).x,
                    facial_landmarks.part(eye_points[3]).y)

    center_top    = midpoint(facial_landmarks.part(eye_points[1]),
                             facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]),
                             facial_landmarks.part(eye_points[4]))

    #calculating distance
    horizontal_length = euclidean_distance(corner_left,corner_right)
    vertical_length = euclidean_distance(center_top,center_bottom)

    ratio = horizontal_length / vertical_length

    return ratio

def run_live_blink_detector():

    #livestream from the webcam
    #cap = cv2.VideoCapture(0)
    cap = cv2.VideoCapture(VIDEO_LOCATION)

    #name of the display window in OpenCV
    # cv2.namedWindow('BlinkDetector')

    #-----Step 3: Face detection with dlib-----
    detector = dlib.get_frontal_face_detector()

    #-----Step 4: Detecting Eyes using landmarks in dlib-----
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    #these landmarks are based on the image above
    left_eye_landmarks  = [36, 37, 38, 39, 40, 41]
    right_eye_landmarks = [42, 43, 44, 45, 46, 47]

    start = time.time()
    count = 0
    prevTime = 0
    numBlinks = 0
    while cap.isOpened():

        #capturing frame
        retval, frame = cap.read()
        count += 1

        #exit the application if frame not found
        if not retval:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        #-----Step 2: converting image to grayscale-----
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #-----Step 3: Face detection with dlib-----
        #detecting faces in the frame
        faces,_,_ = detector.run(image = frame, upsample_num_times = 0,
                           adjust_threshold = 0.0)

        #-----Step 4: Detecting Eyes using landmarks in dlib-----
        for face in faces:

            landmarks = predictor(frame, face)

            #-----Step 5: Calculating blink ratio for one eye-----
            left_eye_ratio  = get_blink_ratio(left_eye_landmarks, landmarks)
            right_eye_ratio = get_blink_ratio(right_eye_landmarks, landmarks)
            blink_ratio     = (left_eye_ratio + right_eye_ratio) / 2

            if blink_ratio > BLINK_RATIO_THRESHOLD and time.time() > prevTime + 1:
                #Blink detected! Do Something!
                cv2.putText(frame,"BLINKING",(10,50), cv2.FONT_HERSHEY_SIMPLEX,
                            2,(255,255,255),2,cv2.LINE_AA)
                numBlinks += 1
                prevTime = time.time()

        #cv2.imwrite("data/" + str(count) + ".jpg", frame)

        continue

        cv2.imshow('BlinkDetector', frame)
        key = cv2.waitKey(1)
        if key == 27:
            break

    elapsed_time = time.time() - start
    print("Sample time:", elapsed_time)
    print("Frames sampled:", count)
    print()
    print("Frames/Sec", count/elapsed_time)
    print("-------------------------------")
    print("Number of Blinks:", numBlinks)
    blinksPerMinute = numBlinks * 60/num_secs
    print("Blinks/Minute", blinksPerMinute)
    print("-------------------------------")

    #releasing the VideoCapture object
    cap.release()
    cv2.destroyAllWindows()

    return blinksPerMinute

def get_frames_per_sec():

    video = cv2.VideoCapture(0);
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

    if int(major_ver)  < 3 :
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else :
        fps = video.get(cv2.CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    num_frames = 120;

    print("Capturing {0} frames".format(num_frames))

    start = time.time()

    for i in range(0, num_frames) :
        ret, frame = video.read()
        cv2.imwrite("data/" + str(i) + ".jpg", frame)

    end = time.time()

    seconds = end - start
    print ("Time taken : {0} seconds".format(seconds))

    fps  = num_frames / seconds

    print("Estimated frames per second : {0}".format(fps))

    video.release()

if __name__ == "__main__":

    print(glob.glob('/dev/tty.*'))

    start = time.time()
    clear_saved_data()
    save_video()
    # print()
    # run_live_blink_detector()
    # print("Total time taken to sample and analyze", num_secs, "secs of the video:", time.time() - start)
