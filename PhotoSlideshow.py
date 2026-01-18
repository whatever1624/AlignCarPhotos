import os
import numpy as np
from moviepy import *
import matplotlib.pyplot as plt

plotHistograms = False
startRot = 330
clockwise = False
fps = 160/60 * 4
fpsVideo = 60
randomness = 2.5
maxResizeFactor1 = 100  # Maximum zoom into the photo for a 2160 crop width reference (photoIndex < 150)
maxResizeFactor2 = 100  # Maximum zoom into the photo for a 2160 crop width reference
slideshowPhotosFolder = r"C:\Users\Willow\PycharmProjects\Sandbox\ELMS Photos (Cropped)"
slideshowOutputFolder = r"C:\Users\Willow\PycharmProjects\Sandbox"
photoFileExtensions = ['jpg', 'jpeg', 'png']


def entryCheckFileType(entry, allowedFileExtensions):
    """Checks entry in directory if it is a file with an allowed file extension"""
    allowedFileExtensions = [ex.lower() for ex in allowedFileExtensions]
    extension = entry.name.split('.')[-1].lower()
    return entry.is_file() and (extension in allowedFileExtensions)


print("Reading photos")
photoFilenames = []
carRotations = []
resizeFactors = []
photoIndexes = []
avgPixelValues = []
numCarTypes = {'LMP2': 0, 'LMP3': 0, 'GT3': 0, 'JSP4': 0, 'JS2R': 0}
numLMP2, numLMP3, numGT3, numJSP4, numJS2R = 0, 0, 0, 0, 0
with os.scandir(slideshowPhotosFolder) as it:
    for entry in it:
        if entryCheckFileType(entry, photoFileExtensions):
            infos = entry.name.split(' ')
            carRotation = float(infos[0])
            resizeFactor = float(infos[1])
            carType = infos[2]
            photoIndex = int(infos[4])
            #imgArr = np.asarray(Image.open(slideshowPhotosFolder + "\\" + entry.name))
            avgPixelValue = 0#np.sum(imgArr) / np.size(imgArr)

            if resizeFactor < maxResizeFactor1 or (photoIndex > 150 and resizeFactor < maxResizeFactor2):
                carRotations.append(carRotation)
                resizeFactors.append(resizeFactor)
                photoIndexes.append(photoIndex)
                avgPixelValues.append(avgPixelValue)
                numCarTypes[carType] += 1
                photoFilenames.append(slideshowPhotosFolder + "\\" + entry.name)
numPhotos = len(photoFilenames)
print("Photo slideshow will be", round(numPhotos / fps, 2), "seconds long at", fps, "FPS")


print("Adding noise to car rotations")
carRotations = np.array(carRotations) + (np.random.rand(numPhotos) * randomness) - (randomness / 2)
indUnder = np.where(carRotations < 0)
carRotations[indUnder] = carRotations[indUnder] + 360
indOver = np.where(carRotations > 360)
carRotations[indOver] = carRotations[indOver] - 360
sortedPhotoFilenames = [photoFilename for carRotation, photoFilename in sorted(zip(carRotations, photoFilenames), key=lambda pair: pair[0])]
if not clockwise:
    sortedPhotoFilenames.reverse()
    carRotations = np.flip(carRotations)


if plotHistograms:
    print('LMP2:', numCarTypes['LMP2'])
    print('LMP3:', numCarTypes['LMP3'])
    print('GT3:', numCarTypes['GT3'])
    print('JSP4:', numCarTypes['JSP4'])
    print('JS2 R:', numCarTypes['JS2R'])

    plt.hist(carRotations, bins=72, range=(0, 360))
    plt.title('Photo Rotation Distribution (' + str(numPhotos) + ' Photos)')
    plt.xlabel('Car Rotation Angle (deg)')
    plt.ylabel('Number of Photos')
    plt.show()

    plt.hist(resizeFactors, bins=50, range=(0, 5))
    plt.title('Photo Resize Factor Distribution (' + str(numPhotos) + ' Photos)')
    plt.xlabel('Photo Resize Factor')
    plt.ylabel('Number of Photos')
    plt.show()

    plt.hist(avgPixelValues, bins=50, range=(0, 256))
    plt.title('Average Pixel Values Distribution (' + str(numPhotos) + ' Photos)')
    plt.xlabel('Average Pixel Value')
    plt.ylabel('Number of Photos')
    plt.show()
    exit()


imgClips = []
clipNumber = 0
clipDuration = 1 / fps
fpsClip = fps * int(1000 / fps)

for i in range(len(sortedPhotoFilenames)):
    if clockwise and startRot <= carRotations[i]:
        clipNumber += 1
        print("Creating clip", clipNumber, "of", numPhotos)
        imgClips.append(ImageClip(sortedPhotoFilenames[i], duration=clipDuration).with_fps(fpsClip))
    elif not clockwise and carRotations[i] <= startRot:
        clipNumber += 1
        print("Creating clip", clipNumber, "of", numPhotos)
        imgClips.append(ImageClip(sortedPhotoFilenames[i], duration=clipDuration).with_fps(fpsClip))

for i in range(len(sortedPhotoFilenames)):
    if clockwise and carRotations[i] < startRot:
        clipNumber += 1
        print("Creating clip", clipNumber, "of", numPhotos)
        imgClips.append(ImageClip(sortedPhotoFilenames[i], duration=clipDuration).with_fps(fpsClip))
    elif not clockwise and startRot < carRotations[i]:
        clipNumber += 1
        print("Creating clip", clipNumber, "of", numPhotos)
        imgClips.append(ImageClip(sortedPhotoFilenames[i], duration=clipDuration).with_fps(fpsClip))

slideshowVideo = concatenate_videoclips(imgClips)
outputFileName = slideshowOutputFolder + "\\LOW BITRATE PhotoSlideshow" + str(numPhotos) + " Noise" + str(randomness) + " " + str(fps)[:4] + " FPS.mp4"
slideshowVideo.write_videofile(outputFileName, fps=fpsVideo, bitrate='1200k')
