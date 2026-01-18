This is a pair of scripts to align car photos (crop and rotate), then combine them into a photo slideshow/montage.

These were created to avoid manually cropping and rotating my photos from ELMS Silverstone 2025 to create the montage below - although it's still a relatively manual process to mark the coordinates of each photo. Because of this, the scripts are quite scrappy and have some hard-coded constants (only the car types racing at ELMS, car dimensions etc.). Whenever I get the opportunity to go to another race weekend, I may consider refactoring this project into something more generalisable. However, it's more likely that I'll train my own machine learning model to align the photos for me automatically now that this project gave me a dataset of almost 800 photos.

https://github.com/user-attachments/assets/d3aece5b-32f8-48d4-b1f6-b34b6f6a067f

### AlignCarPhotos

This has a GUI that iterates through all the photos in the specified folder, to select 4 points on each car.

For side shots: front extremity, front axle centre, rear axle centre, rear extremity.

For front/back shots: left extremity, left fender top, right fender top, right extremity.

There is also a selection for the car type (helps with scaling and calculating rotation). The information for each image is saved to rows in a csv file.

Once the GUI is exited, the images are cropped and rotated to align them using the information saved in the csv file. The aligned photos are saved to 2 different folders - one for the "good" photos, and another for the photos which went out of frame when trying to align. The file names contain the (calculated approximate) heading angle of the car for ordering in the slideshow, the crop ratio for filtering, the car type, whether it was a side or front/back shot, the photo index and the photo name.

*Note: There is also a "normalise brightness" autocontrast function that attempts to normalise the brightness between each photo - but I think this should be removed and this can be done better by batch editing in an actual photo editing program.*

### PhotoSlideshow

This combines the aligned photos into a slideshow/montage at the specified framerate.

There are also some additional features:
- Slight randomisation to the calculated angles as noise to make incorrect approximated rotation angles seem less jarring
- Filter out photos that got too cropped in
- Option to plot histogram distributions of the heading angles, resize factors and average pixel values
