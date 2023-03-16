"""
Framework   : OpenCV Aruco
Description : Calibration of camera and using that for finding pose of multiple markers
Status      : Working
References  :
    1) https://docs.opencv.org/3.4.0/d5/dae/tutorial_aruco_detection.html
    2) https://docs.opencv.org/3.4.3/dc/dbb/tutorial_py_calibration.html
    3) https://docs.opencv.org/3.1.0/d5/dae/tutorial_aruco_detection.html
"""

from cv2 import SOLVEPNP_P3P
import numpy as np
import cv2
import cv2.aruco as aruco
import glob
import math

cap = cv2.VideoCapture('/dev/video0')

# ---------------------- CALIBRATION ---------------------------
# termination criteria for the iterative algorithm
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
# checkerboard of size (7 x 6) is used
objp = np.zeros((6*8, 3), np.float32)
objp[:, :2] = np.mgrid[0:8, 0:6].T.reshape(-1, 2)

# arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

# iterating through all calibration images
# in the folder
images = glob.glob('my_images/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # find the chess board (calibration pattern) corners
    ret, corners = cv2.findChessboardCorners(gray, (8, 6), None)

    # if calibration pattern is found, add object points,
    # image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        # Refine the corners of the detected corners
        corners2 = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (8, 6), corners2, ret)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# ------------------ ARUCO PNP  ----------------------------
arucoDict = aruco.Dictionary_get(aruco.DICT_6X6_250)
arucoParams = cv2.aruco.DetectorParameters_create()

while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 600 pixels
	ret, frame = cap.read()

	# detect ArUco markers in the input frame
	(corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict, parameters=arucoParams)

	# verify *at least* one ArUco marker was detected
	if len(corners) > 0:
		# flatten the ArUco IDs list
		ids = ids.flatten()

		real_points = []
		img_points = []

		# loop over the detected ArUCo corners
		for (markerCorner, markerID) in zip(corners, ids):
			# extract the marker corners (which are always returned
			# in top-left, top-right, bottom-right, and bottom-left
			# order)
			corners = markerCorner.reshape((4, 2))
			(topLeft, topRight, bottomRight, bottomLeft) = corners

			# convert each of the (x, y)-coordinate pairs to integers
			topRight = (int(topRight[0]), int(topRight[1]))
			bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
			bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
			topLeft = (int(topLeft[0]), int(topLeft[1]))

			# draw the bounding box of the ArUCo detection
			cv2.line(frame, topLeft, topRight, (0, 255, 0), 2)
			cv2.line(frame, topRight, bottomRight, (0, 255, 0), 2)
			cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
			cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)

			# compute and draw the center (x, y)-coordinates of the
			# ArUco marker
			cX = int((topLeft[0] + bottomRight[0]) / 2.0)
			cY = int((topLeft[1] + bottomRight[1]) / 2.0)

			if markerID == 23:
				real_points.append([0, 0, 0])
				img_points.append([cX, cY])
			elif markerID == 124:
				real_points.append([2.59, 1.02, 0])
				img_points.append([cX, cY])
			elif markerID == 203:
				real_points.append([-2.91, 1.12, 0])
				img_points.append([cX, cY])
			elif markerID == 62:
				real_points.append([-2.44, -2, 0])
				img_points.append([cX, cY])
			elif markerID == 98:
				real_points.append([3.62, -2.62, 0])
				img_points.append([cX, cY])

			cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)

			# draw the ArUco marker ID on the frame
			cv2.putText(frame, str(markerID),
				(topLeft[0], topLeft[1] - 15),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.5, (0, 255, 0), 2)

		real_points_np = np.array(real_points, dtype=np.float32)
		img_points_np = np.array(img_points, dtype=np.float32)

		# print(real_points_np)
		# print(img_points_np)

		if len(real_points_np) >= 4:
			# _, rVec, tVec = cv2.solvePnP(real_points_np, img_points_np, mtx, dist)
			_, rVec, tVec = cv2.solvePnP(real_points_np, img_points_np, mtx, dist)
			Rt = cv2.Rodrigues(rVec)[0]
			# print(Rt)
			# print(-cv2.transpose(rVec) * tVec)
			R = cv2.transpose(Rt)
			pos = -R * tVec
			print(cv2.transpose(tVec))

	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break


# ------------------ ARUCO ROTATION --------------------------
# while (True):
# 	ret, frame = cap.read()
# 	# if ret returns false, there is likely a problem with the webcam/camera.
# 	# In that case uncomment the below line, which will replace the empty frame
# 	# with a test image used in the opencv docs for aruco at https://www.docs.opencv.org/4.5.3/singlemarkersoriginal.jpg
# 	# frame = cv2.imread('./images/test image.jpg')

# 	# operations on the frame
# 	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 	# set dictionary size depending on the aruco marker selected
# 	aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)

# 	# detector parameters can be set here (List of detection parameters[3])
# 	parameters = aruco.DetectorParameters_create()
# 	parameters.adaptiveThreshConstant = 10

# 	# lists of ids and the corners belonging to each id
# 	corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

# 	# font for displaying text (below)
# 	font = cv2.FONT_HERSHEY_SIMPLEX

# 	# check if the ids list is not empty
# 	# if no check is added the code will crash
# 	if np.all(ids != None):

# 		# estimate pose of each marker and return the values
# 		# rvet and tvec-different from camera coefficients
# 		rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, 1, mtx, dist)

# 		# (rvec-tvec).any() # get rid of that nasty numpy value array error
# 		print("--------------------------------")
# 		for i in range(0, ids.size):
# 			print(ids[i][0], end="")
# 			print(tvec[i])
# 			# draw axis for the aruco markers
# 			cv2.drawFrameAxes(frame, mtx, dist, rvec[i], tvec[i], 0.1)

# 		# draw a square around the markers
# 		aruco.drawDetectedMarkers(frame, corners)

# 		# code to show ids of the marker found
# 		strg = ''
# 		ids.sort()
# 		for i in range(0, ids.size):
# 			strg += str(ids[i][0])+', '

# 		cv2.putText(frame, "Id: " + strg, (0, 64), font, 1, (0,255,0),2,cv2.LINE_AA)

# 	else:
# 		# code to show 'No Ids' when no markers are found
# 		cv2.putText(frame, "No Ids", (0, 64), font, 1, (0,255,0),2,cv2.LINE_AA)

# 	# display the resulting frame
# 	cv2.imshow('frame', frame)
# 	if cv2.waitKey(1) & 0xFF == ord('q'):
# 		break

# # When everything done, release the capture
# cap.release()
# cv2.destroyAllWindows()