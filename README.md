# CT-Scanner_Simulation

Project created during Medical Informatics Course 2022.

## Description

The program (jupyter notebook) simulates the work of a CT Scanner. It takes an image of an already made scan as an input and reconstructs it while performing the series of scans, emulating the actions of a real CT Scanner (Tomograph).

## Requirements

### Languages

* Python 3 (tested on 3.7.8)
* Jupyter Notebook

### Libraries

* numpy
* skimage
* copy
* matplotlib
* ipywidgets
* pydicom

## Usage

The main file ``main.ipynb`` should guid You efficiently. Load required libraries and second cell, choose parameters using user-friendly widgets and watch the magic happen.

While performing, some actions may take some time based on the parameters You've chosen. Watch progress bars to evaluate remaining time.

After marking ``Show steps`` parameter as true you'll be able to watch steb by step scanning and backtracking in the ``Scanning step by step`` and ``Backtracking step by step`` cells.

Finally, the resoults should be evaluated by counting RMSE (Root mean square error) compared with an original image.

### DICOM

## Stats

Script ``compute_stats.py`` allows you to generate detailed step by step reports while changing only one of the main parameters: ``number of scans``, ``number of detectors``, ``opening width``. Take a look into stats directory to get a grasp of the strucutre.

## Reports

Script ``tex_reports_generator.py`` generates easy to copy and paste raport in `.tex`.
