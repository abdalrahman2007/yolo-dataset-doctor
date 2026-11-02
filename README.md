# YOLO Dataset Doctor

A lightweight Python command-line tool for detecting common problems in YOLO object detection datasets.

## Features

- Detect missing label files
- Detect orphan label files
- Validate YOLO annotation format
- Check class IDs against the configured class count
- Validate bounding box coordinates
- Detect invalid or non-finite values
- Generate JSON validation reports
- Support nested image and label directories

## Requirements

- Python 3.10 or newer
- No external dependencies

## Installation

Clone the repository:

    git clone https://github.com/abdalrahman2007/yolo-dataset-doctor.git

    cd yolo-dataset-doctor

## Usage

Run the validator:

    python3 doctor.py /path/to/dataset --classes 22

By default, the tool expects:

    dataset/
    ├── images/
    └── labels/

Custom directory names are supported:

    python3 doctor.py dataset --classes 22 --images images --labels labels

## Example Output

    [MISSING LABEL] dog
    [ORPHAN LABEL] bird

    Images: 2
    Label files: 2
    Issues found: 2

    JSON report saved to: dataset/dataset_doctor_report.json

## Exit Codes

- 0: Dataset checked with no issues
- 1: Dataset checked with validation issues
- 2: Invalid arguments, missing directories, or report-writing failure

## Running Tests

Run the automated test suite:

    python3 -m unittest discover -s tests -v

## License

MIT License
