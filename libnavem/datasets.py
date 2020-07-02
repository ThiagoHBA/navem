# import the necessary packages
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np
import glob
import cv2
import os

from absl import app
from absl import flags

from libnavem.common_flags import FLAGS

def load_navem_attributes(inputPath, remove_repeated=True, samples_equals=1):
	cols = ["path_images", "gyro_z"]
	df = pd.read_csv(inputPath, sep=" ", header=None, names=cols)
	gyro_z = df["gyro_z"].value_counts().keys().tolist()
	counts = df["gyro_z"].value_counts().tolist()
	if remove_repeated:
		for (gyro_z, count) in zip(gyro_z, counts):
			if(count > samples_equals):
				idxs = df[df["gyro_z"] == gyro_z].index
				df.drop(idxs[0], inplace=True)
	#programPause = input("Press the <ENTER> key to continue save train and test...")
	return df

def load_navem_images(data_frame):
	# initialize our images array (i.e., the house images themselves)
	cols = ["path_images", "gyro_z"]
	df = pd.read_csv("./datasets/labels/" + FLAGS.dataset + ".txt", sep=" ", header=None, names=cols)
	#df = pd.read_csv("/home/david/Área de Trabalho/navem_keras/datasets/labels/dataset_cel_resized_64_64_rgb.txt", sep=" ", header=None, names=cols)
	images = []
	for i in data_frame.values:
		#print("./datasets/images/" + FLAGS.dataset + "/" + i[0])
		image = cv2.imread("./datasets/images/" + FLAGS.dataset + "/" + i[0])
		#image = cv2.imread("./datasets/images/dataset_cel_resized_64_64_rgb/" + i[0])
		images.append(image)
	#programPause = input("Press the <ENTER> key to continue save train and test...")
	return np.array(images)

def load_house_attributes(inputPath):
	# initialize the list of column names in the CSV file and then
	# load it using Pandas
	cols = ["bedrooms", "bathrooms", "area", "zipcode", "price"]
	df = pd.read_csv(inputPath, sep=" ", header=None, names=cols)

	# determine (1) the unique zip codes and (2) the number of data
	# points with each zip code
	zipcodes = df["zipcode"].value_counts().keys().tolist()
	counts = df["zipcode"].value_counts().tolist()

	# loop over each of the unique zip codes and their corresponding
	# count
	for (zipcode, count) in zip(zipcodes, counts):
		# the zip code counts for our housing dataset is *extremely*
		# unbalanced (some only having 1 or 2 houses per zip code)
		# so let's sanitize our data by removing any houses with less
		# than 25 houses per zip code
		if count < 25:
			idxs = df[df["zipcode"] == zipcode].index
			df.drop(idxs, inplace=True)

	# return the data frame
	return df

def process_house_attributes(df, train, test):
	# initialize the column names of the continuous data
	continuous = ["bedrooms", "bathrooms", "area"]

	# performin min-max scaling each continuous feature column to
	# the range [0, 1]
	cs = MinMaxScaler()
	trainContinuous = cs.fit_transform(train[continuous])
	testContinuous = cs.transform(test[continuous])

	# one-hot encode the zip code categorical data (by definition of
	# one-hot encoing, all output features are now in the range [0, 1])
	zipBinarizer = LabelBinarizer().fit(df["zipcode"])
	trainCategorical = zipBinarizer.transform(train["zipcode"])
	testCategorical = zipBinarizer.transform(test["zipcode"])

	# construct our training and testing data points by concatenating
	# the categorical features with the continuous features
	trainX = np.hstack([trainCategorical, trainContinuous])
	testX = np.hstack([testCategorical, testContinuous])

	# return the concatenated training and testing data
	return (trainX, testX)

def load_house_images(df, inputPath):
	# initialize our images array (i.e., the house images themselves)
	images = []

	# loop over the indexes of the houses
	for i in df.index.values:
		# find the four images for the house and sort the file paths,
		# ensuring the four are always in the *same order*
		basePath = os.path.sep.join([inputPath, "{}_*".format(i + 1)])
		housePaths = sorted(list(glob.glob(basePath)))

		# initialize our list of input images along with the output image
		# after *combining* the four input images
		inputImages = []
		outputImage = np.zeros((64, 64, 3), dtype="uint8")

		# loop over the input house paths
		for housePath in housePaths:
			# load the input image, resize it to be 32 32, and then
			# update the list of input images
			image = cv2.imread(housePath)
			image = cv2.resize(image, (32, 32))
			inputImages.append(image)

		# tile the four input images in the output image such the first
		# image goes in the top-right corner, the second image in the
		# top-left corner, the third image in the bottom-right corner,
		# and the final image in the bottom-left corner
		outputImage[0:32, 0:32] = inputImages[0]
		outputImage[0:32, 32:64] = inputImages[1]
		outputImage[32:64, 32:64] = inputImages[2]
		outputImage[32:64, 0:32] = inputImages[3]

		# add the tiled image to our set of images the network will be
		# trained on
		images.append(outputImage)

	# return our set of images
	return np.array(images)
