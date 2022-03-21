import numpy as np
from skimage.draw import line_nd
import cv2
from copy import deepcopy
from skimage.exposure import rescale_intensity
import time
import os
import matplotlib.pyplot as plt
from torch import gather

DEFAULT_VAL = 180
MODIF_SCN = 1
MODIF_DET = 2
MODIF_OPN = 3


def find_circle_described(input_img):
    img_heigth, img_width = np.shape(input_img)

    cx = int(img_width / 2)
    cy = int(img_heigth / 2)

    radius = int(np.floor(0.5 * np.sqrt(img_heigth**2 + img_width**2)))

    return cx, cy, radius


def scan(input_img, cx, cy, radius, scans, detectors, opening):
    img_heigth, img_width = np.shape(input_img)
    alpha = 360 / scans
    step = alpha
    alpha = 0
    n = detectors
    l = opening

    E = []
    D = []

    sinogram = []

    for _ in range(scans):
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
                if x >= 0 and y < img_heigth and y >= 0 and x < img_width:
                    brightness += input_img[y][x]
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
                if x >= 0 and y < img_heigth and y >= 0 and x < img_width:
                    backshots[-1][y][x] += sinogram[i][j]

    return backshots[-1]


def calculate_rmse(input_img, final_result):
    RMSE = 0.0
    for i in range(input_img.shape[0]):
        for j in range(input_img.shape[1]):
            RMSE += (float(input_img[i][j]) - float(final_result[i][j]))**2
    RMSE = RMSE / (input_img.shape[0]*input_img.shape[1])
    RMSE = RMSE**(0.5)

    return RMSE


if __name__ == '__main__':
    probe_name = "CT_ScoutView_large"
    probe_ext = "jpg"

    stats_dir_path = "stats/" + probe_name

    try:
        os.mkdir("stats")
    except:
        pass

    try:
        os.mkdir(stats_dir_path)
    except:
        pass

    gathered = open(stats_dir_path + "/gathered.csv", "w+")
    gathered.write("probe;scans;detectors;opening;RMSE;time\n")

    total_time_start = time.time()

    for modify_parameter in range(1, 4):
        scans = DEFAULT_VAL
        detectors = DEFAULT_VAL
        opening = DEFAULT_VAL

        if modify_parameter == MODIF_SCN:
            scans = 90
        if modify_parameter == MODIF_DET:
            detectors = 90
        if modify_parameter == MODIF_OPN:
            opening = 45

        while True:
            start_time = time.time()

            input_img = cv2.imread(
                "./example_photos/" + probe_name + "." + probe_ext)

            if len(np.shape(input_img)) == 3:
                input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)

            kernel_size = 21

            print("Computing:", probe_name, scans,
                  detectors, opening, kernel_size)

            cx, cy, radius = find_circle_described(input_img)

            sinogram, E, D = scan(input_img, cx, cy, radius,
                                  scans, detectors, opening)

            sinogram = filter_sinogram(sinogram, kernel_size)

            final_result = backtrace(sinogram, E, D, detectors)

            input_image = rescale_intensity(
                input_img, out_range=(0, 255)).astype(np.uint8)

            p_low, p_high = np.percentile(final_result, (10, 99.9))

            final_result = rescale_intensity(
                final_result, in_range=(p_low, p_high), out_range=(0, 255)).astype(np.uint8)

            RMSE = calculate_rmse(input_img, final_result)

            end_time = time.time()

            partial = open(stats_dir_path + "/partial-" + probe_name + "-" + str(modify_parameter) + "-" + str(scans) +
                           "-" + str(detectors) + "-" + str(opening) + ".txt", "w+")

            partial.write("Probe: " + str(probe_name) + "\n")
            partial.write("Scans: " + str(scans) + "\n")
            partial.write("Detectors: " + str(detectors) + "\n")
            partial.write("Opening: " + str(opening) + "\n")
            partial.write("RMSE: " + str(RMSE) + "\n")
            partial.write("Time: %s\n" % (end_time - start_time))
            partial.close()

            gathered.write(probe_name + ";" + str(scans) + ";" + str(detectors) + ";" + str(
                opening) + ";" + str(RMSE) + ";" + "%s" % (end_time - start_time) + "\n")

            print("Saving: " + stats_dir_path + "/input-" + probe_name + "-" + str(modify_parameter) + "-" + str(scans) +
                  "-" + str(detectors) + "-" + str(opening) + "." + probe_ext)
            cv2.imwrite(stats_dir_path + "/input-" + probe_name + "-" + str(modify_parameter) + "-" + str(scans) +
                        "-" + str(detectors) + "-" + str(opening) + "." + probe_ext, input_img)

            print("Saving: " + stats_dir_path + "/output-" + probe_name + "-" + str(modify_parameter) + "-" + str(scans) +
                  "-" + str(detectors) + "-" + str(opening) + ".png")
            cv2.imwrite(stats_dir_path + "/output-" + probe_name + "-" + str(modify_parameter) + "-" + str(scans) +
                        "-" + str(detectors) + "-" + str(opening) + ".png", final_result)

            if modify_parameter == MODIF_SCN:
                scans += 90
            if modify_parameter == MODIF_DET:
                detectors += 90
            if modify_parameter == MODIF_OPN:
                opening += 45

            if scans > 720 or detectors > 720 or opening > 270:
                break

    total_time_end = time.time()
    time_spent = open(stats_dir_path + "/time.txt", "w+")
    time_spent.write("Total time: %s" % (total_time_end - total_time_start))
    time_spent.close()

    gathered.close()
