import cv2
import numpy as np

def sharpen_image(image, strength=1.5, kernel_size=(5,5)):
    img = cv2.imread(image)
    # blur dulu
    blurred = cv2.GaussianBlur(img, kernel_size, 0)

    # sharpen: original + (original - blur)
    sharpened = cv2.addWeighted(img, 1 + strength, blurred, -strength, 0)

    return sharpened

def sharpen_kernel(image):


    kernel = np.array([
        [0, -1, 0],
        [-1, 5,-1],
        [0, -1, 0]
    ])

    return cv2.filter2D(image, -1, kernel)

# img = cv2.imread("foto_data/add_capturep_462.jpg")

# result = sharpen_image(img, strength=2)

# cv2.imwrite("preprocessingimage/outputsharped.jpg", result)
# result = sharpen_kernel(img)
# cv2.imwrite("preprocessingimage/outputkernel.jpg", result)
