import os
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import scipy.ndimage
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
from matplotlib.widgets import Button, RadioButtons

# Settings
startPhotoGUI = 1
photosFolder = r"C:\Users\Willow\PycharmProjects\Sandbox\ELMS Photos"
cropPhotosFolder = r"C:\Users\Willow\PycharmProjects\Sandbox\ELMS Photos (Cropped)"
cropOutOfFrameFolder = r"C:\Users\Willow\PycharmProjects\Sandbox\ELMS Photos (Out of Frame)"
photoFileExtensions = ['jpg', 'jpeg', 'png']
photosCoordsFilepath = r"C:\Users\Willow\PycharmProjects\Sandbox\Photos Coords.csv"

cropWidth = 1080
cropHeight = 1350
height = 0.42                       # Base height of the centre of the axle-projected extremity line
frontBackShotExtraHeight = 0.05     # Extra height to add if the shot is front-on/back-on
imgWidthScale = 5.25                # Distance in metres from the left of the image to the right for consistent scale between photos
smoothScaleMultSigma = 15           # 0 for true image scale, set this higher for more equal car width in the image frame
globalRotOffset = 0                 # Rotation offset at 90 degrees, and negative this at 270 degrees
sideShotRotOffset = -3              # Rotation offset in degrees to align side shots with front/back shots when car is diagonal
frontBackShotRotOffset = 5          # Rotation offset in degrees to align front/back shots with side shots when car is diagonal

imgRotSideShotLUT = []
imgRotFrontBackShotLUT = []
degToRad = np.pi / 180
for deg in range(0, 361):
    theta = deg * degToRad
    globalRot = globalRotOffset * np.sin(theta)
    imgRotSideShotLUT.append([deg, sideShotRotOffset * np.sin(2 * theta) + globalRot])
    imgRotFrontBackShotLUT.append([deg, frontBackShotRotOffset * np.sin(theta) ** 2 + globalRot])


def entryCheckFileType(entry, allowedFileExtensions):
    """Checks entry in directory if it is a file with an allowed file extension"""
    allowedFileExtensions = [ex.lower() for ex in allowedFileExtensions]
    extension = entry.name.split('.')[-1].lower()
    return entry.is_file() and (extension in allowedFileExtensions)


def findPhotoCoordsEntry(photoEntryName):
    index = np.where(photosCoordsFileData[:,0] == photoEntryName)[0]
    if index.size > 0:
        return index[0]
    else:
        return None


def updatePhotosCoordsFile():
    file = open(photosCoordsFilepath, 'w')
    dataString = ''
    for line in photosCoordsFileData:
        lineString = ''
        for item in line:
            lineString += item + ','
        dataString += lineString[:-1] + '\n'
    file.write(dataString)
    print("Saved to file")


def refreshPhoto():
    """Refresh photo plotted"""
    global xlimImg, ylimImg, ax, imgSaveData, selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive

    # Remove all plot artists
    for artist in [img, frontAxlePlotArtist, rearAxlePlotArtist, frontExtremityPlotArtist, rearExtremityPlotArtist]:
        if artist:
            artist.pop().remove()

    # Update photoEntry
    photoEntry = sortedPhotoEntries[photoIndex]
    titleString = "Photo " + str(photoIndex + 1) + " of " + str(len(sortedPhotoEntries)) + ": " + photoEntry.name
    print("\n" + titleString)

    # Read photoEntry to array and calculate image axis limits
    imgData = np.asarray(ImageOps.exif_transpose(Image.open(photoEntry)))
    xlimImg = [-0.5, np.size(imgData, axis=1) - 0.5]
    ylimImg = [-0.5, np.size(imgData, axis=0) - 0.5]

    # Plot image
    ax.set_title(titleString)
    ax.set_xlim(xlimImg)
    ax.set_ylim((ylimImg[1], ylimImg[0]))
    img.append(ax.imshow(imgData))

    # Search if photo is in file data and load coords if so
    index = findPhotoCoordsEntry(photoEntry.name)
    if index:
        imgSaveData = {'Filename': str(photosCoordsFileData[index][0]),
                       'Front Axle': [float(photosCoordsFileData[index][1]), float(photosCoordsFileData[index][2])],
                       'Rear Axle': [float(photosCoordsFileData[index][3]), float(photosCoordsFileData[index][4])],
                       'Front Extremity': [float(photosCoordsFileData[index][5]), float(photosCoordsFileData[index][6])],
                       'Rear Extremity': [float(photosCoordsFileData[index][7]), float(photosCoordsFileData[index][8])],
                       'Side Shot': photosCoordsFileData[index][9],
                       'Car Type': photosCoordsFileData[index][10]}
    else:
        imgSaveData = {'Filename': photoEntry.name,
                       'Front Axle': [],
                       'Rear Axle': [],
                       'Front Extremity': [],
                       'Rear Extremity': [],
                       'Side Shot': 'True',
                       'Car Type': 'None'}

    # GUI stuff
    selectFrontAxleActive = False
    selectRearAxleActive = False
    selectFrontExtremityActive = False
    selectRearExtremityActive = False
    buttonSelectFrontAxle.color = buttonColor
    buttonSelectRearAxle.color = buttonColor
    buttonSelectFrontExtremity.color = buttonColor
    buttonSelectRearExtremity.color = buttonColor

    # Update GUI labels
    if imgSaveData['Side Shot'] == 'True':
        buttonSelectFrontAxle.label.set_text('Select Front Axle Centre')
        buttonSelectRearAxle.label.set_text('Select Rear Axle Centre')
        buttonSelectFrontExtremity.label.set_text('Select Front Extremity')
        buttonSelectRearExtremity.label.set_text('Select Rear Extremity')
    else:
        buttonSelectFrontAxle.label.set_text('Select Left Fender Top')
        buttonSelectRearAxle.label.set_text('Select Right Fender Top')
        buttonSelectFrontExtremity.label.set_text('Select Left Extremity')
        buttonSelectRearExtremity.label.set_text('Select Right Extremity')
    buttonSideShot.label.set_text('Side Shot: ' + imgSaveData['Side Shot'])
    buttonSideShot.color = buttonColor if imgSaveData['Side Shot'] == 'True' else 'red'
    buttonSideShot.hovercolor = buttonHoverColor if imgSaveData['Side Shot'] == 'True' else 'tab:red'
    carTypeRadioIndex = {'None': 0, 'LMP2': 1, 'LMP3': 2, 'GT3': 3, 'JSP4': 4, 'JS2 R': 5}
    radioCarType.set_active(carTypeRadioIndex[imgSaveData['Car Type']])
    radioCarType.activecolor = 'red' if imgSaveData['Car Type'] == 'None' else 'blue'

    # Plot coordinate plot artists
    plotPhotoCoords()


def plotPhotoCoords():
    # Colours
    if imgSaveData['Side Shot'] == 'True':
        cFA = '#ff7f0e'
        cRA = '#1f77b4'
        cFE = '#d62728'
        cRE = '#17becf'
    else:
        cFA = '#d62728'
        cRA = '#2ca02c'
        cFE = '#ff7f0e'
        cRE = '#17becf'

    # Plot axle plot artists
    if imgSaveData['Front Axle']:
        frontAxlePlotArtist.append(ax.scatter(imgSaveData['Front Axle'][0], imgSaveData['Front Axle'][1], c=cFA))
    if imgSaveData['Rear Axle']:
        rearAxlePlotArtist.append(ax.scatter(imgSaveData['Rear Axle'][0], imgSaveData['Rear Axle'][1], c=cRA))

    # Plot extremity plot artists - perpendicular line if axle coords exist, otherwise scatter points
    if imgSaveData['Front Axle'] and imgSaveData['Rear Axle'] and imgSaveData['Front Axle'] != imgSaveData['Rear Axle']:
        diff = np.array(imgSaveData['Front Axle']) - np.array(imgSaveData['Rear Axle'])
        vector = np.array([-diff[1], diff[0]]) * (max(np.diff(xlimImg)[0], np.diff(ylimImg)[0]) / np.linalg.norm(diff))
        if imgSaveData['Front Extremity']:
            xLine = [imgSaveData['Front Extremity'][0] - vector[0], imgSaveData['Front Extremity'][0] + vector[0]]
            yLine = [imgSaveData['Front Extremity'][1] - vector[1], imgSaveData['Front Extremity'][1] + vector[1]]
            frontExtremityPlotArtist.append(ax.plot(xLine, yLine, c='C1')[0])
        if imgSaveData['Rear Extremity']:
            xLine = [imgSaveData['Rear Extremity'][0] - vector[0], imgSaveData['Rear Extremity'][0] + vector[0]]
            yLine = [imgSaveData['Rear Extremity'][1] - vector[1], imgSaveData['Rear Extremity'][1] + vector[1]]
            rearExtremityPlotArtist.append(ax.plot(xLine, yLine, c='C0')[0])
    else:
        if imgSaveData['Front Extremity']:
            frontExtremityPlotArtist.append(ax.scatter(imgSaveData['Front Extremity'][0], imgSaveData['Front Extremity'][1], c=cFE))
        if imgSaveData['Rear Extremity']:
            rearExtremityPlotArtist.append(ax.scatter(imgSaveData['Rear Extremity'][0], imgSaveData['Rear Extremity'][1], c=cRE))


def zoom(event):
    """Zoom in and out of a matplotlib graph with mouse scroll, limited by maximum zoom out"""
    rate = 0.2
    if ax := event.inaxes:
        # Get current limits and range
        xlim = list(ax.get_xlim())
        ylim = list(ax.get_ylim())
        xrange = xlim[1] - xlim[0]
        yrange = ylim[1] - ylim[0]

        # Check if limits are reversed
        xlimReversed = xrange < 0
        ylimReversed = yrange < 0
        if xlimReversed:
            xrange = -xrange
            xlim.reverse()
        if ylimReversed:
            yrange = -yrange
            ylim.reverse()

        # Get cursor coordinates and normalised by current limits
        xCursor = event.xdata
        yCursor = event.ydata
        xCursorRatio = np.interp(xCursor, xlim, [0, 1])
        yCursorRatio = np.interp(yCursor, ylim, [0, 1])

        # Calculate change in limits (only if xCursor and yCursor are valid coordinates)
        if event.button == 'up':
            # Zoom in (scroll up)
            xlim[0] += xrange * rate * xCursorRatio
            xlim[1] -= xrange * rate * (1 - xCursorRatio)
            ylim[0] += yrange * rate * yCursorRatio
            ylim[1] -= yrange * rate * (1 - yCursorRatio)
        elif event.button == 'down':
            # Zoom out (scroll down)
            xlim[0] -= xrange * rate * xCursorRatio
            xlim[1] += xrange * rate * (1 - xCursorRatio)
            ylim[0] -= yrange * rate * yCursorRatio
            ylim[1] += yrange * rate * (1 - yCursorRatio)
            # Shift zoom out to other side if exceeding image limits
            if xlim[0] < xlimImg[0]:
                xlim[1] += xlimImg[0] - xlim[0]
                xlim[0] = xlimImg[0]
            if xlim[1] > xlimImg[1]:
                xlim[0] -= xlim[1] - xlimImg[1]
                xlim[1] = xlimImg[1]
            if ylim[0] < ylimImg[0]:
                ylim[1] += ylimImg[0] - ylim[0]
                ylim[0] = ylimImg[0]
            if ylim[1] > ylimImg[1]:
                ylim[0] -= ylim[1] - ylimImg[1]
                ylim[1] = ylimImg[1]
            # If still exceeding image limits, set limits to image limits
            if xlim[0] < xlimImg[0] or ylim[0] < ylimImg[0]:
                xlim = xlimImg.copy()
                ylim = ylimImg.copy()

        # Set new limits
        if xlimReversed:
            xlim.reverse()
        if ylimReversed:
            ylim.reverse()
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)


def selectCoords(event):
    """Select image coordinates by clicking, then save coord and GUI stuff depending on button state"""
    global imgSaveData, selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive

    if event.inaxes == ax:
        coords = [float(event.xdata), float(event.ydata)]

        # Update image save data coordinates
        if selectFrontAxleActive:
            imgSaveData['Front Axle'] = coords
            selectFrontAxleActive = False
        elif selectRearAxleActive:
            imgSaveData['Rear Axle'] = coords
            selectRearAxleActive = False
        elif selectFrontExtremityActive:
            imgSaveData['Front Extremity'] = coords
            selectFrontExtremityActive = False
        elif selectRearExtremityActive:
            imgSaveData['Rear Extremity'] = coords
            selectRearExtremityActive = False

        # Update GUI
        buttonSelectFrontAxle.color = buttonHoverColor if selectFrontAxleActive else buttonColor
        buttonSelectRearAxle.color = buttonHoverColor if selectRearAxleActive else buttonColor
        buttonSelectFrontExtremity.color = buttonHoverColor if selectFrontExtremityActive else buttonColor
        buttonSelectRearExtremity.color = buttonHoverColor if selectRearExtremityActive else buttonColor

        # Remove coordinate plot artists
        for artist in [frontAxlePlotArtist, rearAxlePlotArtist, frontExtremityPlotArtist, rearExtremityPlotArtist]:
            if artist:
                artist.pop().remove()
        # Plot new coordinate plot artists
        plotPhotoCoords()


def prevPhoto(event):
    global photosCoordsFileData, photoIndex, xlimImg, ylimImg, ax

    if all([imgSaveData[i] for i in imgSaveData.keys()]):
        # Save photo coords and update file
        entry = np.array([imgSaveData['Filename'],
                          str(imgSaveData['Front Axle'][0]),
                          str(imgSaveData['Front Axle'][1]),
                          str(imgSaveData['Rear Axle'][0]),
                          str(imgSaveData['Rear Axle'][1]),
                          str(imgSaveData['Front Extremity'][0]),
                          str(imgSaveData['Front Extremity'][1]),
                          str(imgSaveData['Rear Extremity'][0]),
                          str(imgSaveData['Rear Extremity'][1]),
                          imgSaveData['Side Shot'],
                          imgSaveData['Car Type']])
        index = findPhotoCoordsEntry(imgSaveData['Filename'])
        if index:
            photosCoordsFileData[index] = entry
        else:
            photosCoordsFileData = np.vstack((photosCoordsFileData, entry))
        updatePhotosCoordsFile()

    photoIndex -= 1
    if photoIndex < 0:
        print("Reached end of photos")
        plt.close()
    else:
        refreshPhoto()


def skipPhoto(event):
    """Marks photo as skipped by making setting all coords to the centre of the image"""
    photoCentreCoords = [np.diff(xlimImg)[0] / 2, np.diff(ylimImg)[0] / 2]
    imgSaveData['Front Axle'] = photoCentreCoords
    imgSaveData['Rear Axle'] = photoCentreCoords
    imgSaveData['Front Extremity'] = photoCentreCoords
    imgSaveData['Rear Extremity'] = photoCentreCoords

    # Remove coordinate plot artists
    for artist in [frontAxlePlotArtist, rearAxlePlotArtist, frontExtremityPlotArtist, rearExtremityPlotArtist]:
        if artist:
            artist.pop().remove()
    # Plot new coordinate plot artists
    plotPhotoCoords()


def nextPhoto(event):
    global photosCoordsFileData, photoIndex, xlimImg, ylimImg, ax

    if all([imgSaveData[i] for i in imgSaveData.keys()]):
        # Save photo coords and update file
        entry = np.array([imgSaveData['Filename'],
                          str(imgSaveData['Front Axle'][0]),
                          str(imgSaveData['Front Axle'][1]),
                          str(imgSaveData['Rear Axle'][0]),
                          str(imgSaveData['Rear Axle'][1]),
                          str(imgSaveData['Front Extremity'][0]),
                          str(imgSaveData['Front Extremity'][1]),
                          str(imgSaveData['Rear Extremity'][0]),
                          str(imgSaveData['Rear Extremity'][1]),
                          imgSaveData['Side Shot'],
                          imgSaveData['Car Type']])
        index = findPhotoCoordsEntry(imgSaveData['Filename'])
        if index:
            photosCoordsFileData[index] = entry
        else:
            photosCoordsFileData = np.vstack((photosCoordsFileData, entry))
        updatePhotosCoordsFile()

        photoIndex += 1
        if photoIndex >= len(sortedPhotoEntries):
            print("Reached end of photos")
            plt.close()
        else:
            refreshPhoto()
    else:
        print(imgSaveData)
        print("Select all coordinates first")


def selectFrontAxle(event):
    global selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive
    selectFrontAxleActive = not selectFrontAxleActive
    selectRearAxleActive = False
    selectFrontExtremityActive = False
    selectRearExtremityActive = False
    buttonSelectFrontAxle.color = buttonHoverColor if selectFrontAxleActive else buttonColor
    buttonSelectRearAxle.color = buttonHoverColor if selectRearAxleActive else buttonColor
    buttonSelectFrontExtremity.color = buttonHoverColor if selectFrontExtremityActive else buttonColor
    buttonSelectRearExtremity.color = buttonHoverColor if selectRearExtremityActive else buttonColor


def selectRearAxle(event):
    global selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive
    selectFrontAxleActive = False
    selectRearAxleActive = not selectRearAxleActive
    selectFrontExtremityActive = False
    selectRearExtremityActive = False
    buttonSelectFrontAxle.color = buttonHoverColor if selectFrontAxleActive else buttonColor
    buttonSelectRearAxle.color = buttonHoverColor if selectRearAxleActive else buttonColor
    buttonSelectFrontExtremity.color = buttonHoverColor if selectFrontExtremityActive else buttonColor
    buttonSelectRearExtremity.color = buttonHoverColor if selectRearExtremityActive else buttonColor


def selectFrontExtremity(event):
    global selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive
    selectFrontAxleActive = False
    selectRearAxleActive = False
    selectFrontExtremityActive = not selectFrontExtremityActive
    selectRearExtremityActive = False
    buttonSelectFrontAxle.color = buttonHoverColor if selectFrontAxleActive else buttonColor
    buttonSelectRearAxle.color = buttonHoverColor if selectRearAxleActive else buttonColor
    buttonSelectFrontExtremity.color = buttonHoverColor if selectFrontExtremityActive else buttonColor
    buttonSelectRearExtremity.color = buttonHoverColor if selectRearExtremityActive else buttonColor


def selectRearExtremity(event):
    global selectFrontAxleActive, selectRearAxleActive, selectFrontExtremityActive, selectRearExtremityActive
    selectFrontAxleActive = False
    selectRearAxleActive = False
    selectFrontExtremityActive = False
    selectRearExtremityActive = not selectRearExtremityActive
    buttonSelectFrontAxle.color = buttonHoverColor if selectFrontAxleActive else buttonColor
    buttonSelectRearAxle.color = buttonHoverColor if selectRearAxleActive else buttonColor
    buttonSelectFrontExtremity.color = buttonHoverColor if selectFrontExtremityActive else buttonColor
    buttonSelectRearExtremity.color = buttonHoverColor if selectRearExtremityActive else buttonColor


def toggleSideShot(event):
    if imgSaveData['Side Shot'] == 'True':
        imgSaveData['Side Shot'] = 'False'
        buttonSelectFrontAxle.label.set_text('Select Left Fender Top')
        buttonSelectRearAxle.label.set_text('Select Right Fender Top')
        buttonSelectFrontExtremity.label.set_text('Select Left Extremity')
        buttonSelectRearExtremity.label.set_text('Select Right Extremity')
    else:
        imgSaveData['Side Shot'] = 'True'
        buttonSelectFrontAxle.label.set_text('Select Front Axle Centre')
        buttonSelectRearAxle.label.set_text('Select Rear Axle Centre')
        buttonSelectFrontExtremity.label.set_text('Select Front Extremity')
        buttonSelectRearExtremity.label.set_text('Select Rear Extremity')
    buttonSideShot.label.set_text("Side Shot: " + imgSaveData['Side Shot'])
    buttonSideShot.color = buttonColor if imgSaveData['Side Shot'] == 'True' else 'red'


def selectCarType(label):
    imgSaveData['Car Type'] = label
    radioCarType.activecolor = 'red' if imgSaveData['Car Type'] == 'None' else 'blue'


# Photos sorted by date/time, only include photos in the directory itself not any subfolders
print("Reading photos")
photoEntries = []
photoDateTimes = []
with os.scandir(photosFolder) as it:
    for entry in it:
        if entryCheckFileType(entry, photoFileExtensions):
            photoEntries.append(entry)
            photoDateTimes.append(Image.open(entry).getexif().get(306))
sortedPhotoEntries = [photoEntry for photoDateTime, photoEntry in sorted(zip(photoDateTimes, photoEntries), key=lambda pair: pair[0])]


# Read/write save files and variables
photosCoordsFileData = [line.split(',') for line in open(photosCoordsFilepath, 'r').read().strip().split('\n')]
firstLine = ['Filename', 'Front Axle or Left Tyre X', 'Front Axle or Left Tyre Y', 'Rear Axle or Right Tyre X', 'Rear Axle or Right Tyre Y', 'Front or Left Extremity X', 'Front or Left Extremity Y', 'Rear or Right Extremity X', 'Rear or Right Extremity Y', 'Side Shot', 'Car Type']
if photosCoordsFileData[0] == ['']:
    photosCoordsFileData[0] = firstLine
elif photosCoordsFileData[0] != firstLine:
    print("Invalid first line of photosCoordsFileData")
    print(photosCoordsFileData[0])
    exit()
photosCoordsFileData = np.array(photosCoordsFileData)
imgSaveData = {}


# GUI variables
photoIndex = min(startPhotoGUI, len(sortedPhotoEntries)) - 1
photoEntry = sortedPhotoEntries[photoIndex]
img = []
xlimImg = [-1e10, 1e10]
ylimImg = [-1e10, 1e10]
frontAxlePlotArtist = []
rearAxlePlotArtist = []
frontExtremityPlotArtist = []
rearExtremityPlotArtist = []


# GUI setup
print("Setting up GUI")
mplstyle.use('fast')
plt.ion()
plt.style.use('dark_background')
fig, ax = plt.subplots()
fig.canvas.manager.set_window_title('Photo coordinate selector GUI: Close to begin photo rotate and crop process')
fig.canvas.mpl_connect('scroll_event', zoom)
fig.canvas.mpl_connect('button_press_event', selectCoords)

buttonColor = '0.15'
buttonHoverColor = '0.3'

buttonPrevPhotoAx = plt.axes((0.025, 0.925, 0.2, 0.05))
buttonPrevPhoto = Button(buttonPrevPhotoAx, 'Previous Photo', color=buttonColor, hovercolor=buttonHoverColor)
buttonPrevPhoto.on_clicked(prevPhoto)

buttonSkipPhotoAx = plt.axes((0.4, 0.925, 0.2, 0.05))
buttonSkipPhoto = Button(buttonSkipPhotoAx, 'Skip Photo', color=buttonColor, hovercolor=buttonHoverColor)
buttonSkipPhoto.on_clicked(skipPhoto)

buttonNextPhotoAx = plt.axes((0.775, 0.925, 0.2, 0.05))
buttonNextPhoto = Button(buttonNextPhotoAx, 'Next Photo', color=buttonColor, hovercolor=buttonHoverColor)
buttonNextPhoto.on_clicked(nextPhoto)

selectFrontAxleActive = False
buttonSelectFrontAxleAx = plt.axes((0.025, 0.675, 0.15, 0.075))
buttonSelectFrontAxle = Button(buttonSelectFrontAxleAx, 'Select Front Axle\nor Left Fender', color=buttonColor, hovercolor=buttonHoverColor)
buttonSelectFrontAxle.on_clicked(selectFrontAxle)

selectRearAxleActive = False
buttonSelectRearAxleAx = plt.axes((0.025, 0.5, 0.15, 0.075))
buttonSelectRearAxle = Button(buttonSelectRearAxleAx, 'Select Rear Axle\nor Right Fender', color=buttonColor, hovercolor=buttonHoverColor)
buttonSelectRearAxle.on_clicked(selectRearAxle)

selectFrontExtremityActive = False
buttonSelectFrontExtremityAx = plt.axes((0.025, 0.325, 0.15, 0.075))
buttonSelectFrontExtremity = Button(buttonSelectFrontExtremityAx, 'Select Front Extremity\nor Left Extremity', color=buttonColor, hovercolor=buttonHoverColor)
buttonSelectFrontExtremity.on_clicked(selectFrontExtremity)

selectRearExtremityActive = False
buttonSelectRearExtremityAx = plt.axes((0.025, 0.15, 0.15, 0.075))
buttonSelectRearExtremity = Button(buttonSelectRearExtremityAx, 'Select Rear Extremity\nor Right Extremity', color=buttonColor, hovercolor=buttonHoverColor)
buttonSelectRearExtremity.on_clicked(selectRearExtremity)

buttonSideShotAx = plt.axes((0.825, 0.675, 0.15, 0.075))
buttonSideShot = Button(buttonSideShotAx, 'Side Shot: ?', color=buttonColor, hovercolor=buttonHoverColor)
buttonSideShot.on_clicked(toggleSideShot)

radioCarTypeAx = plt.axes((0.825, 0.15, 0.15, 0.5))
radioCarType = RadioButtons(radioCarTypeAx, ('None', 'LMP2', 'LMP3', 'GT3', 'JSP4', 'JS2 R'), radio_props={'s': 128, 'edgecolors': 'white'})
radioCarType.on_clicked(selectCarType)


# Start GUI and stay in GUI until the figure is closed
print("Starting GUI")
refreshPhoto()
plt.show(block=True)
# Code from now on executes once the GUI is closed


# Save current data if all imgSaveData is present
print("\nSorting image data and saving all to file")
if all([imgSaveData[i] for i in imgSaveData.keys()]):
    entry = np.array([imgSaveData['Filename'],
                      str(imgSaveData['Front Axle'][0]),
                      str(imgSaveData['Front Axle'][1]),
                      str(imgSaveData['Rear Axle'][0]),
                      str(imgSaveData['Rear Axle'][1]),
                      str(imgSaveData['Front Extremity'][0]),
                      str(imgSaveData['Front Extremity'][1]),
                      str(imgSaveData['Rear Extremity'][0]),
                      str(imgSaveData['Rear Extremity'][1]),
                      imgSaveData['Side Shot'],
                      imgSaveData['Car Type']])
    index = findPhotoCoordsEntry(imgSaveData['Filename'])
    if index:
        photosCoordsFileData[index] = entry
    else:
        photosCoordsFileData = np.vstack((photosCoordsFileData, entry))


# Sort photo coords file data then save to file
photosCoordsFileDataSorted = [firstLine]
indexes = []
for i in range(len(sortedPhotoEntries)):
    index = findPhotoCoordsEntry(sortedPhotoEntries[i].name)
    if index:
        photosCoordsFileDataSorted.append(photosCoordsFileData[index])
        indexes.append(index)
for i in range(1, len(photosCoordsFileData)):
    if i not in indexes:
        photosCoordsFileDataSorted.append(photosCoordsFileData[i])
photosCoordsFileData = np.array(photosCoordsFileDataSorted)
updatePhotosCoordsFile()


# Precalculate rotation LUTs
corrFractionGT = 0.85
carInfoLMP2 = {'Width': 1.9,
               'Wheelbase': 3,
               'Front Overhang': 0.964,
               'Rear Overhang': 0.737}
carInfoLMP3 = {'Width': 1.9,
               'Wheelbase': 2.86,
               'Front Overhang': 1.013,
               'Rear Overhang': 0.794}
carInfoGT3 = {'Width': 2.05,
               'Wheelbase': sum([2.63, 2.763, 2.6, 2.507]) / 4,
               'Front Overhang': sum([0.971, 0.939, 1.262, 1.103]) / 4,
               'Rear Overhang': sum([1.025, 0.858, 0.811, 1.093]) / 4}  # Merc, Aston, Ferrari, Porsche
carInfoJSP4 = carInfoLMP3  # idk
carInfoJS2R = {'Width': 1.9,
               'Wheelbase': 2.68,
               'Front Overhang': 0.9,
               'Rear Overhang': 0.9}  # Guesstimated front/rear overhang
carInfos = {'LMP2': carInfoLMP2, 'LMP3': carInfoLMP3, 'GT3': carInfoGT3, 'JSP4': carInfoJSP4, 'JS2 R': carInfoJS2R}
sideRotLUTs = {}        # Keys are the car types, contains dict with keys Rotation, Extremity Front Ratio, Extremity Length
frontBackRotLUTs = {}   # Keys are the car types, contains dict with keys Rotation, Width Extremity Ratio, Left Extremity Ratio, Extremity Length
for key in carInfos.keys():
    width = carInfos[key]['Width']
    widthCorr = width * corrFractionGT if key in ['GT3', 'JS2 R'] else width
    wheelbase = carInfos[key]['Wheelbase']
    frontOverhang = carInfos[key]['Front Overhang']
    rearOverhang = carInfos[key]['Rear Overhang']
    totalLength = wheelbase + frontOverhang + rearOverhang
    frontOverhangCorr = frontOverhang * corrFractionGT if key in ['GT3', 'JS2 R'] else frontOverhang
    rearOverhangCorr = rearOverhang * corrFractionGT if key in ['GT3', 'JS2 R'] else rearOverhang
    totalLengthCorr = wheelbase + frontOverhangCorr + rearOverhangCorr
    sideRotLUT = {'Rotation': [], 'Extremity Front Ratio': [], 'Extremity Length': []}
    frontBackRotLUT = {'Rotation': [], 'Width Extremity Ratio': [], 'Left Extremity Ratio': [], 'Extremity Length': []}
    for deg in range(361):
        # Rotation angle 0 when car is driving away, positive rotation means rotating clockwise (like heading angle)
        theta = deg * degToRad
        s = abs(np.sin(theta))
        c = abs(np.cos(theta))

        # Side shots
        axleLength = wheelbase * s
        extremityLength = totalLength * s + widthCorr * c
        axleExtremityRatio = axleLength / extremityLength
        frontExtremityLength = frontOverhang * s + widthCorr * c
        rearExtremityLength = rearOverhang * s + widthCorr * c
        if deg < 90:        # Car pointing away and to the right
            frontExtremityLength = frontOverhangCorr * s
            rearExtremityLength = rearOverhangCorr * s + width * c
        elif deg < 270:     # Car pointing towards
            frontExtremityLength = frontOverhangCorr * s + width * c
            rearExtremityLength = rearOverhangCorr * s
        else:               # Car pointing away and to the left
            frontExtremityLength = frontOverhangCorr * s
            rearExtremityLength = rearOverhangCorr * s + width * c
        sideRotLUT['Rotation'].append(deg)
        sideRotLUT['Extremity Front Ratio'].append(frontExtremityLength / (frontExtremityLength + rearExtremityLength))
        sideRotLUT['Extremity Length'].append(extremityLength)

        # Front/back shots
        widthLength = width * c
        extremityLength = width * c + totalLengthCorr * s
        if deg < 90:        # Car pointing away and to the right, rear axle used as ref
            leftExtremityLength = rearOverhangCorr * s
            rightExtremityLength = (wheelbase + frontOverhangCorr) * s
        elif deg < 180:     # Car pointing towards and to the right, front axle used as ref
            leftExtremityLength = frontOverhangCorr * s
            rightExtremityLength = (wheelbase + rearOverhangCorr) * s
        elif deg < 270:     # Car pointing towards and to the left, front axle used as ref
            leftExtremityLength = (wheelbase + rearOverhangCorr) * s
            rightExtremityLength = frontOverhangCorr * s
        else:               # Car pointing away and to the left, rear axle used as ref
            leftExtremityLength = (wheelbase + frontOverhangCorr) * s
            rightExtremityLength = rearOverhangCorr * s
        if (leftExtremityLength + rightExtremityLength) != 0:  # Protect against divide by 0
            leftExtremityRatio = leftExtremityLength / (leftExtremityLength + rightExtremityLength)
        else:
            leftExtremityRatio = 0
        frontBackRotLUT['Rotation'].append(deg)
        frontBackRotLUT['Width Extremity Ratio'].append(widthLength / extremityLength)
        frontBackRotLUT['Left Extremity Ratio'].append(leftExtremityRatio)
        frontBackRotLUT['Extremity Length'].append(extremityLength)

    # Smooth extremity length
    sideRotLUT['Extremity Length'] = list(scipy.ndimage.gaussian_filter1d(sideRotLUT['Extremity Length'], smoothScaleMultSigma))
    frontBackRotLUT['Extremity Length'] = list(scipy.ndimage.gaussian_filter1d(frontBackRotLUT['Extremity Length'], smoothScaleMultSigma))

    # Once rotation sweep has been completed, append the LUT to the LUTs dictionary
    sideRotLUTs[key] = sideRotLUT
    frontBackRotLUTs[key] = frontBackRotLUT


# Align photos
print("\nAligning photos")
imgRotSideShotLUT = np.array(imgRotSideShotLUT)
imgRotFrontBackShotLUT = np.array(imgRotFrontBackShotLUT)
for photoIndex in range(len(sortedPhotoEntries)):
    photoEntry = sortedPhotoEntries[photoIndex]

    # Find photo coords entry
    index = findPhotoCoordsEntry(photoEntry.name)

    # Flags if the photo entry is not valid
    skipFlag = False
    if index:
        img = ImageOps.exif_transpose(Image.open(photoEntry))
        filename = str(photosCoordsFileData[index][0])
        frontAxleCoords = np.array([float(photosCoordsFileData[index][1]), float(photosCoordsFileData[index][2])])
        rearAxleCoords = np.array([float(photosCoordsFileData[index][3]), float(photosCoordsFileData[index][4])])
        frontExtremityCoords = np.array([float(photosCoordsFileData[index][5]), float(photosCoordsFileData[index][6])])
        rearExtremityCoords = np.array([float(photosCoordsFileData[index][7]), float(photosCoordsFileData[index][8])])
        isSideShot = True if photosCoordsFileData[index][9] == 'True' else False
        carType = photosCoordsFileData[index][10]
        if carType == 'None':
            skipFlag = True
            print("Skipping photo", photoEntry.name, "- No car type")
        if np.all(frontAxleCoords == rearAxleCoords):
            skipFlag = True
            print("Skipping photo", photoEntry.name, "- Marked as skip")
    else:
        skipFlag = True
        print("Skipping photo", photoEntry.name, "- No coords")

    if not skipFlag:
        # Project extremity coordinates to axle line
        axleLine = frontAxleCoords - rearAxleCoords
        axleLineLength = np.linalg.norm(axleLine)
        axleLineUnitVec = axleLine / axleLineLength
        frontExtremityCoords = frontAxleCoords + axleLineUnitVec * np.dot(frontExtremityCoords - frontAxleCoords, axleLine / axleLineLength)
        rearExtremityCoords = rearAxleCoords + axleLineUnitVec * np.dot(rearExtremityCoords - rearAxleCoords, axleLine / axleLineLength)

        # Estimate rotation of the car then swap coordinates so that left/right refer to left/right of the image not the car
        if isSideShot:
            frontExtremityLength = np.linalg.norm(frontExtremityCoords - frontAxleCoords)
            rearExtremityLength = np.linalg.norm(rearExtremityCoords - rearAxleCoords)
            frontExtremityRatio = frontExtremityLength / (frontExtremityLength + rearExtremityLength)
            if frontAxleCoords[0] > rearAxleCoords[0]:
                # Front axle on the right so 0 <= deg <= 180, frontExtremityRatio increasing with rotation
                rot = np.interp(frontExtremityRatio, sideRotLUTs[carType]['Extremity Front Ratio'][0:181], sideRotLUTs[carType]['Rotation'][0:181])
            else:
                # Front axle on the left so 180 <= deg <= 360, frontExtremityRatio decreasing with rotation
                rot = np.interp(frontExtremityRatio, np.flip(sideRotLUTs[carType]['Extremity Front Ratio'][180:361]), np.flip(sideRotLUTs[carType]['Rotation'][180:361]))
            extremityLength = np.interp(rot, sideRotLUTs[carType]['Rotation'], sideRotLUTs[carType]['Extremity Length'])
            leftExtremityCoords = frontExtremityCoords if rot > 180 else rearExtremityCoords
            rightExtremityCoords = rearExtremityCoords if rot > 180 else frontExtremityCoords
            lineAngle = np.interp(rot, imgRotSideShotLUT[:, 0], imgRotSideShotLUT[:, 1]) * degToRad
            lineY = (1 - height) * cropHeight
        else:
            # Front/back shot
            widthExtremityRatio = axleLineLength / np.linalg.norm(frontExtremityCoords - rearExtremityCoords)
            leftExtremityLength = np.linalg.norm(frontExtremityCoords - frontAxleCoords)
            rightExtremityLength = np.linalg.norm(rearExtremityCoords - rearAxleCoords)
            leftExtremityRatio = leftExtremityLength / (leftExtremityLength + rightExtremityLength)
            if frontAxleCoords[0] < rearAxleCoords[0]:
                # Left is on left of photo so 0 <= deg <= 90 or 270 <= deg <= 360
                leftExtremityRatioRef = np.array([frontBackRotLUTs[carType]['Left Extremity Ratio'][45], frontBackRotLUTs[carType]['Left Extremity Ratio'][315]])
                if (np.abs(leftExtremityRatio - leftExtremityRatioRef)).argmin() == 0:
                    # 0 <= deg <= 90, widthExtremityRatio decreasing with rotation
                    rot = np.interp(widthExtremityRatio, np.flip(frontBackRotLUTs[carType]['Width Extremity Ratio'][0:91]), np.flip(frontBackRotLUTs[carType]['Rotation'][0:91]))
                else:
                    # 270 <= deg <= 360, widthExtremityRatio increasing with rotation
                    rot = np.interp(widthExtremityRatio, frontBackRotLUTs[carType]['Width Extremity Ratio'][270:361], frontBackRotLUTs[carType]['Rotation'][270:361])
            else:
                # Right is on left of photo so 90 <= deg <= 270
                leftExtremityRatioRef = np.array([frontBackRotLUTs[carType]['Left Extremity Ratio'][135], frontBackRotLUTs[carType]['Left Extremity Ratio'][225]])
                if (np.abs(leftExtremityRatio - leftExtremityRatioRef)).argmin() == 0:
                    # 90 <= deg <= 180, widthExtremityRatio increasing with rotation
                    rot = np.interp(widthExtremityRatio, frontBackRotLUTs[carType]['Width Extremity Ratio'][90:181], frontBackRotLUTs[carType]['Rotation'][90:181])
                else:
                    # 180 <= deg <= 270, widthExtremityRatio decreasing with rotation
                    rot = np.interp(widthExtremityRatio, np.flip(frontBackRotLUTs[carType]['Width Extremity Ratio'][180:271]), np.flip(frontBackRotLUTs[carType]['Rotation'][180:271]))
            extremityLength = np.interp(rot, frontBackRotLUTs[carType]['Rotation'], frontBackRotLUTs[carType]['Extremity Length'])
            leftExtremityCoords = rearExtremityCoords if 90 < rot < 270 else frontExtremityCoords
            rightExtremityCoords = frontExtremityCoords if 90 < rot < 270 else rearExtremityCoords
            lineAngle = np.interp(rot, imgRotFrontBackShotLUT[:, 0], imgRotFrontBackShotLUT[:, 1]) * degToRad
            lineY = (1 - height - frontBackShotExtraHeight) * cropHeight

        # Calculate points that the axle/tyre-projected extremity coordinates must be transformed onto
        extremityImgWidth = extremityLength / imgWidthScale * cropWidth
        leftExtremityTargetX = (cropWidth - extremityImgWidth) / 2
        leftExtremityTargetY = lineY - np.sin(lineAngle) * extremityImgWidth / 2
        leftExtremityCoordsTarget = np.array([leftExtremityTargetX, leftExtremityTargetY])
        rightExtremityTargetX = leftExtremityTargetX + extremityImgWidth
        rightExtremityTargetY = lineY + np.sin(lineAngle) * extremityImgWidth / 2
        rightExtremityCoordsTarget = np.array([rightExtremityTargetX, rightExtremityTargetY])
        extremityLineTarget = rightExtremityCoordsTarget - leftExtremityCoordsTarget
        extremityLineTargetLength = np.linalg.norm(extremityLineTarget)

        # # Resize photo
        extremityLine = rightExtremityCoords - leftExtremityCoords
        extremityLineLength = np.linalg.norm(extremityLine)
        resizeFactor = extremityLineTargetLength / extremityLineLength
        resize = (int(round(img.width * resizeFactor, 0)), int(round(img.height * resizeFactor, 0)))
        imgResize = img.resize(size=resize, resample=Image.Resampling.LANCZOS)

        # Calculate image rotation such that axleLine is coincident with extremityLineTarget
        rotateAngle = float(-np.atan2(extremityLine[0] * extremityLineTarget[1] - extremityLine[1] * extremityLineTarget[0], extremityLine[0] * extremityLineTarget[0] + extremityLine[1] * extremityLineTarget[1]))
        rotateAngleDeg = rotateAngle / degToRad

        # Calculate image translation such that leftExtremity is at leftExtremityCoordsTarget (and by extension, rightExtremity is at rightExtremityCoordsTarget)
        c, s = np.cos(-rotateAngle), np.sin(-rotateAngle)
        rotMatrix = np.array([[c, -s], [s, c]])
        leftExtremityCoordsResizeRot = np.matvec(rotMatrix, leftExtremityCoords * resizeFactor)
        translateVector = leftExtremityCoordsTarget - leftExtremityCoordsResizeRot

        # Rotate, translate and crop image
        imgResizeRotTrans = imgResize.rotate(angle=rotateAngleDeg, resample=Image.Resampling.BICUBIC, center=(0, 0), translate=translateVector, fillcolor=(0, 255, 0))
        imgResizeRotTransCrop = imgResizeRotTrans.crop((0, 0, cropWidth, cropHeight))

        # Save image to folder with some info at the front of the name
        if rot < 10:
            infoString = '00' + str(rot)
        elif rot < 100:
            infoString = '0' + str(rot)
        else:
            infoString = str(rot)
        infoString = infoString[:5] + ' ' + str(resizeFactor * (2160 / cropWidth))[:5]
        infoString += ' ' + carType.replace(' ', '') + (' SS' if isSideShot else ' FB')
        infoString += ' ' + str(photoIndex)

        # Check if the photo was rotated/translated out of bounds
        numPxOutOfFrame = 0
        for x in range(cropWidth):
            for y in range(cropHeight):
                if imgResizeRotTransCrop.getpixel((x, y)) == (0, 255, 0) or imgResizeRotTransCrop.getpixel((x, y)) == (0, 0, 0):
                    numPxOutOfFrame += 1 if (cropHeight - y) > cropHeight / 20 else 0.75

        # Fill out of frame pixels with black if not too much is out of frame
        if numPxOutOfFrame == 0:
            outOfFrame = False
        elif numPxOutOfFrame < 0.15 * cropWidth * cropHeight:
            imgResizeRotTrans = imgResize.rotate(angle=rotateAngleDeg, resample=Image.Resampling.BICUBIC, center=(0, 0), translate=translateVector, fillcolor=(0, 0, 0))
            imgResizeRotTransCrop = imgResizeRotTrans.crop((0, 0, cropWidth, cropHeight))
            outOfFrame = False
        else:
            outOfFrame = True

        # Normalise brightness
        imgResizeRotTransCropBrightness = ImageOps.autocontrast(imgResizeRotTransCrop, 1, preserve_tone=True)

        # Save photos
        print("Saving aligned photo:", infoString + " " + photoEntry.name.split('.')[0] + ".png" + "\t\t\t" + str(round(numPxOutOfFrame / cropWidth / cropHeight, 3)))
        if outOfFrame:
            imgResizeRotTransCropBrightness.save(cropOutOfFrameFolder + "\\" + infoString + " " + photoEntry.name.split('.')[0] + ".png")
        else:
            imgResizeRotTransCropBrightness.save(cropPhotosFolder + "\\" + infoString + " " + photoEntry.name.split('.')[0] + ".png")
