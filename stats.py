import numpy as np
from skimage.draw import line_nd
import cv2
from copy import deepcopy
from skimage.exposure import rescale_intensity
import time
import os
import matplotlib.pyplot as plt


def find_circle_described(img):
    # Image shape
    img_heigth, img_width = np.shape(img)

    # Center of mass
    cx = int(img_heigth / 2)
    cy = int(img_width / 2)

    # Radius
    radius = int(np.floor(0.5 * np.sqrt(img_heigth**2 + img_width**2)))

    return cx, cy, radius


def scan(input_img, cx, cy, radius, scans, detectors, opening):
    alpha = 360 / scans
    step = alpha
    n = detectors
    l = opening

    E = []
    D = []

    sinogram = []

    img_heigth, img_width = np.shape(input_img)

    for s in range(scans):
        # Calculating emiter's position
        xe = radius * np.cos(np.deg2rad(alpha))
        ye = radius * np.sin(np.deg2rad(alpha))

        E.append((int(cx + xe), int(cy + (-1)*ye)))

        D.append([])
        sinogram.append([])

        for i in range(n):
            # Calculating detector's position
            xd = radius * np.cos(np.deg2rad(alpha + 180 -
                                 l / 2 + i * (l / (n-1))))
            yd = radius * np.sin(np.deg2rad(alpha + 180 -
                                 l / 2 + i * (l / (n-1))))

            D[-1].append((int(xd + cx), int((-1)*yd + cy)))

            # Calculating points of the line
            line_x_points, line_y_points = line_nd(E[-1], D[-1][-1])

            brightness = 0
            sumof = 0

            for (x, y) in zip(line_x_points, line_y_points):
                # Calculating mean brightness
                if x >= 0 and x < img_heigth and y >= 0 and y < img_width:
                    brightness += input_img[x][y]
                    sumof += 1

            # Adding results to sinogram
            if sumof != 0:
                brightness = brightness / sumof
            else:
                brightness = 0
            sinogram[-1].append(brightness)

        alpha += step

    return sinogram, E, D


def filter_sinogram(sinogram, kernel_size):
    sinogram = np.array(sinogram)

    kernel = []
    for k in range(-int(np.floor(kernel_size/2)), int(np.ceil(kernel_size/2))):
        if k == 0:
            kernel.append(1)
        else:
            if k % 2 == 0:
                kernel.append(0)
            else:
                kernel.append((-4 / np.pi**2)/(k**2))

    for i in range(len(sinogram)):
        sinogram[i] = np.convolve(sinogram[i], kernel, mode='same')

    return sinogram


def backtrace(sinogram, E, D, n):
    img_heigth, img_width = np.shape(input_img)

    backshots = []
    blank_image = np.zeros((img_heigth, img_width))

    for i in range(len(sinogram)):
        if i == 0:
            backshots.append(deepcopy(blank_image))
        else:
            backshots.append(deepcopy(backshots[-1]))
        for j in range(n):
            line_x_points, line_y_points = line_nd(E[i], D[i][j])
            for (x, y) in zip(line_x_points, line_y_points):
                # Calculating mean brightness
                if x >= 0 and x < img_heigth and y >= 0 and y < img_width:
                    backshots[-1][x][y] += sinogram[i][j]

    return backshots[-1]


def calculate_rmse(input_img, final_result):
    RMSE = 0
    input_img = rescale_intensity(input_img, (0, 255))

    for i in range(len(input_img)):
        for j in range(len(input_img[i])):
            RMSE += (input_img[i][j] - final_result[i][j])**2

    RMSE = RMSE / (len(input_img) * len(input_img[0]))
    RMSE = np.sqrt(RMSE)

    return RMSE


if __name__ == '__main__':
    probe_name = "Kropka"
    probe_ext = "jpg"

    for scans in range(90, 721, 90):
        for detectors in range(90, 721, 90):
            for opening in range(45, 271, 45):
                start_time = time.time()

                input_img = cv2.imread(
                    "./example_photos/" + probe_name + "." + probe_ext)

                if len(np.shape(input_img)) == 3:
                    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)

                kernel_size = 11

                print("Computing:", probe_name, scans,
                      detectors, opening, kernel_size)

                cx, cy, radius = find_circle_described(input_img)
                sinogram, E, D = scan(input_img, cx, cy, radius, scans, detectors, opening)
                
                sinogram = filter_sinogram(sinogram, kernel_size)
                
                final_result = backtrace(sinogram, E, D, detectors)
                final_result = rescale_intensity(final_result, (0, 255))
                
                RMSE = calculate_rmse(input_img, final_result)

                result_dir_path = "results/" + probe_name + "-" + str(scans) + "-" + str(detectors) + "-" + str(opening)
                os.mkdir(result_dir_path)
                
                results = open(result_dir_path + "/stats.txt", "w+")

                results.write("Probe: " + str(probe_name) + "\n")
                results.write("Scans: " + str(scans) + "\n")
                results.write("Detectors: " + str(detectors) + "\n")
                results.write("Opening: " + str(opening) + "\n")
                results.write("RMSE: " + str(RMSE) + "\n")
                results.write("Time: %s s\n" % (time.time() - start_time))
                
                results.close()
                
                cv2.imwrite(result_dir_path + "/input." + probe_ext, input_img)
                cv2.imwrite(result_dir_path + "/output.jpg", final_result)
