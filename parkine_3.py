''' This program detects the entry and exit of cars in the parkingspaces in a parking lot.
It uses the yaml file included to detect the corners and draw contours based on which a console is displayed showing
the parking lot where the masked rectangles change colour from green to red if a car is detected and shows the number
of empty parking spots '''


import yaml
import numpy as np
import cv2
import webbrowser
fn = "WhatsApp Video 2017-12-09 at 8.07.15 PM.mp4"
# parking lot position data file
fn_yaml = "parkSquare2.yml"
# output vidoe filename
fn_out = "output4.avi"
config = {'save_video': False,# flag for save video file
          'text_overlay': True,# display text for parking lot status
          'parking_overlay': True,#displaying for parking status
          'parking_id_overlay': True,# parking lot status
          'parking_detection': True,# parking or no parking detction
          'motion_detection': False,# car detection
          'pedestrian_detction': False,#human or other detection
          'min_area_motion_contour': 150,# threshold for detection of vehicle
          'park_laplacian_th': 2.5,# thresohold for parking status
          'park_sec_to_wait': 5,# delay time
          'start_frame': 0}  # first frame position

# Set capture device or file
cap = cv2.VideoCapture(1)
video_info = {'fps': cap.get(cv2.CAP_PROP_FPS),# frame per a second
              'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),# frame width
              'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),# frame height
              'fourcc': cap.get(cv2.CAP_PROP_FOURCC),# format of video compression
              'num_of_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}# the number of frames
cap.set(cv2.CAP_PROP_POS_FRAMES, config['start_frame'])  # jump to frame

# Define the codec and create VideoWriter object
if config['save_video']:
    fourcc = cv2.VideoWriter_fourcc('C', 'R', 'A',
                                    'M')  # options: ('P','I','M','1'), ('D','I','V','X'), ('M','J','P','G'), ('X','V','I','D')
    out = cv2.VideoWriter(fn_out, -1, 25.0,  # video_info['fps'],
                          (video_info['width'], video_info['height']))

# initialize the HOG descriptor/person detector
if config['pedestrian_detction']:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# Create Background subtractor
if config['motion_detection']:
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=True)
    # fgbg = cv2.createBackgroundSubtractorKNN(history=100, dist2Threshold=800.0, detectShadows=False)

# Read YAML data (parking space polygons)
with open(fn_yaml, 'r') as stream:
    parking_data = yaml.load(stream)
# detection of parking contour, bound rectagle of each parking, parking mask
parking_contours = []
parking_bounding_rects = []
parking_mask = []
#read parking postion data from parking data
for park in parking_data:
    points = np.array(park['points'])
    rect = cv2.boundingRect(points)
    points_shifted = points.copy()
    points_shifted[:, 0] = points[:, 0] - rect[0]  # shift contour to roi
    points_shifted[:, 1] = points[:, 1] - rect[1]  # shift contour to roi
    parking_contours.append(points)
    parking_bounding_rects.append(rect)
    mask = cv2.drawContours(np.zeros((rect[3], rect[2]), dtype=np.uint8), [points_shifted], contourIdx=-1,
                            color=255, thickness=-1, lineType=cv2.LINE_8)
    mask = mask == 255
    parking_mask.append(mask)
# intialize of parking status
kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))  # morphological kernel
# kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)) # morphological kernel
kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 19))
parking_status = [False] * len(parking_data)
parking_buffer = [None] * len(parking_data)
# parking status updating in real time
while (cap.isOpened()):
    # Read frame-by-frame
    # captureing each frame
    video_cur_pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0  # Current position of the video file in seconds
    video_cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)  # Index of the frame to be decoded/captured next
    ret, frame = cap.read()
    if ret == False:
        print("Capture Error")
        break

    # frame_gray = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
    # Background Subtraction
    frame_blur = cv2.GaussianBlur(frame.copy(), (5, 5), 3)# apply gausion blur to given frame
    frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)# convert color image into gray image
    frame_out = frame.copy()# output frame
    #cv2.imshow('frame', frame_out)
    # cv2.imshow('background mask', bw)
    #k = cv2.waitKey(1)
    # Draw Overlay; display frame number on screen
    if config['text_overlay']:
        str_on_frame = "%d/%d" % (video_cur_frame, video_info['num_of_frames'])
        # cv2.putText(frame_out, str_on_frame, (5, 30), cv2.FONT_HERSHEY_SIMPLEX,
        #             0.8, (0, 255, 255), 2, cv2.LINE_AA)

    if config['motion_detection']:
        # apply blur
        fgmask = fgbg.apply(frame_blur)
        bw = np.uint8(fgmask == 255) * 255# binarization
        bw = cv2.erode(bw, kernel_erode, iterations=1)# image erode
        bw = cv2.dilate(bw, kernel_dilate, iterations=1)# image dilation
        # contour detection of frame
        (_, cnts, _) = cv2.findContours(bw.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < config['min_area_motion_contour']:
                continue
            (x, y, w, h) = cv2.boundingRect(c)#for moving vehicle, detects rectangle of moving object
            cv2.rectangle(frame_out, (x, y), (x + w, y + h), (255, 0, 0), 2)# display rectangle of moving object
    # parking status detection
    if config['parking_detection']:
        for ind, park in enumerate(parking_data):# for each parking lot, check the parking status
            points = np.array(park['points'])# four corners of each parking lot
            rect = parking_bounding_rects[ind]# make rectangle with four corners
            roi_gray = frame_gray[rect[1]:(rect[1] + rect[3]),# crop rectangle part
                       rect[0]:(rect[0] + rect[2])]  # crop roi for faster calcluation
            laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)# apply laplacian operation
            points[:, 0] = points[:, 0] - rect[0]  # shift contour to roi
            points[:, 1] = points[:, 1] - rect[1]# shift contour to roi
            delta = np.mean(np.abs(laplacian * parking_mask[ind]))# parameter for detectinog of parking statu
            #  check parking is  or nots
            status = delta < config['park_laplacian_th']
            # If detected a change in parking status, save the current time
            if status != parking_status[ind] and parking_buffer[ind] == None:
                parking_buffer[ind] = video_cur_pos
            # If status is still different than the one saved and counter is open
            elif status != parking_status[ind] and parking_buffer[ind] != None:
                #if video_cur_pos - parking_buffer[ind] > config['park_sec_to_wait']:
                parking_status[ind] = status
                parking_buffer[ind] = None
            # If status is still same and counter is open
            elif status == parking_status[ind] and parking_buffer[ind] != None:
                # if video_cur_pos - parking_buffer[ind] > config['park_sec_to_wait']:
                parking_buffer[ind] = None
                # print("#%d: %.2f" % (ind, delta))
                # print(parking_status)

    if config['parking_overlay']:# checing parking status in real time
        available_num=0# the number of availabile parking lot
        #htmlstr=''
        # f = open('Parking.html', 'w')
        # message = """<html>
        # <head></head>
        # <body>"""
        # # <p>Hello World!</p></body>
        # # </html>"""
        for ind, park in enumerate(parking_data):# counting the available parking lots
            points = np.array(park['points'])# the corners of each parking
            if parking_status[ind]:# check the parking status
                color = (0, 255, 0)# the color of avaliable parking lot
                available_num+=1# add one for avalaible paring number
                #message+="""<p>spot """+str(ind)+""" is available!</p>"""
            else:
                color = (0, 0, 255)# not available parking's color
            cx = int((points[0][0] + points[3][0]+points[1][0] + points[2][0]) / 4)# center of x-axis in parking
            cy = int((points[0][1] + points[3][1]+points[1][1] + points[2][1]) / 4)# center of y-axis in parking
            cv2.circle(frame_out, (cx, cy), 6, color, -1)# draw cirlce fopr each parking
            # draw rectanlge for each parking
            cv2.line(frame_out, (points[0][0], points[0][1]), (points[1][0], points[1][1]), (255, 255, 0), 2)
            cv2.line(frame_out, (points[1][0], points[1][1]), (points[2][0], points[2][1]), (255, 255, 0), 2)
            cv2.line(frame_out, (points[2][0], points[2][1]), (points[3][0], points[3][1]), (255, 255, 0), 2)
            # cv2.drawContours(frame_out, [points], contourIdx=-1,
            #                  color=color, thickness=2, lineType=cv2.LINE_8)
            #
            # moments = cv2.moments(points)
            # centroid = (int(moments['m10'] / moments['m00']) - 3, int(moments['m01'] / moments['m00']) + 3)
            # cv2.putText(frame_out, str(park['id']), (centroid[0] + 1, centroid[1] + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
            #             (255, 255, 255), 1, cv2.LINE_AA)
            # cv2.putText(frame_out, str(park['id']), (centroid[0] - 1, centroid[1] - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
            #             (255, 255, 255), 1, cv2.LINE_AA)
            # cv2.putText(frame_out, str(park['id']), (centroid[0] + 1, centroid[1] - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
            #             (255, 255, 255), 1, cv2.LINE_AA)
            # cv2.putText(frame_out, str(park['id']), (centroid[0] - 1, centroid[1] + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.3,
            #             (255, 255, 255), 1, cv2.LINE_AA)
            # cv2.putText(frame_out, str(park['id']), centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1, cv2.LINE_AA)
        # draw the available number on screen
        cv2.putText(frame_out, str(available_num)+' spots are available now.', (5, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 255), 2, cv2.LINE_AA)
        # message += """<p>""" + str(available_num) + """ spots are available!</p></body></html>"""
        # f.write(message)
        # f.close()

    if config['pedestrian_detction']:
        # detect people in the image
        (rects, weights) = hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.05)

        # draw the original bounding boxes
        for (x, y, w, h) in rects:
            cv2.rectangle(frame_out, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # write the output frame
    if config['save_video']:
        if video_cur_frame % 35 == 0:  # take every 30 frames
            out.write(frame_out)# write video

            # Display video
    cv2.imshow('frame', frame_out)# display each frame
    # cv2.imshow('background mask', bw)
    k = cv2.waitKey(1)
    if k == ord('q'):# if user click key 'q', program will be closed
        break
    elif k == ord('c'):# if user click key "c', frame can be saved in special file folder
        cv2.imwrite('frame%d.jpg' % video_cur_frame, frame_out)
    elif k == ord('j'):# if user click key'j', then jth frame will be jumped
        cap.set(cv2.CAP_PROP_POS_FRAMES, video_cur_frame + 10000)  # jump to frame

cap.release()# release camera
if config['save_video']: out.release()# save captured video
cv2.destroyAllWindows()# release screen

