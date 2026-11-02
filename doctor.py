#!/usr/bin/env python3

import argparse
from pathlib import Path
import json
import math

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"
}


def check_label_file(path: Path, num_classes: int | None = None):

    errors = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"Cannot read file: {exc}"]

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        parts = line.split()

        if len(parts) != 5:
            errors.append(
                f"Line {line_number}: expected 5 values, got {len(parts)}"
            )
            continue

        try:
            class_value = float(parts[0])
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"Line {line_number}: non-numeric value")
            continue

        if not all(math.isfinite(v) for v in [class_value, *coords]):
            errors.append(
                f"Line {line_number}: values must be finite numbers"
            )
            continue

        if not class_value.is_integer() or class_value < 0:
            errors.append(f"Line {line_number}: invalid class ID")
        elif num_classes is not None and class_value >= num_classes:
            errors.append(
                f"Line {line_number}: class ID {int(class_value)} "
                f"is outside 0–{num_classes - 1}"
            )

        for name, value in zip(
            ("x_center", "y_center", "width", "height"), coords
        ):
            if not 0 <= value <= 1:
                errors.append(
                    f"Line {line_number}: {name}={value} is outside [0, 1]"
                )

        if coords[2] <= 0 or coords[3] <= 0:
            errors.append(
                f"Line {line_number}: width and height must be positive"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Check YOLO detection datasets for common problems."
    )
    parser.add_argument("dataset", help="Dataset root folder")
    parser.add_argument("--classes", type=int, default=None)
    parser.add_argument("--images", default="images", help="Images folder name")
    parser.add_argument("--labels", default="labels", help="Labels folder name")
    args = parser.parse_args()

    if args.classes is not None and args.classes < 1:
        parser.error("--classes must be at least 1")

    root = Path(args.dataset)
    images_dir = root / args.images
    labels_dir = root / args.labels

    if not images_dir.is_dir() or not labels_dir.is_dir():
        parser.error(
            f"Expected both '{images_dir}' and '{labels_dir}' directories."
        )

    images = sorted(
        p for p in images_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    labels = sorted(labels_dir.rglob("*.txt"))

    label_by_name = {p.relative_to(labels_dir).with_suffix(""): p for p in labels}
    image_keys = {p.relative_to(images_dir).with_suffix("") for p in images}

    missing_labels = sorted(image_keys - label_by_name.keys())
    orphan_labels = sorted(label_by_name.keys() - image_keys)

    issues = 0
    report = []

    for key in missing_labels:
        print(f"[MISSING LABEL] {key}")
        report.append({
            "type": "missing_label",
            "item": str(key),
            "message": f"No label file found for image '{key}'"
        })
        issues += 1

    for key in orphan_labels:
        print(f"[ORPHAN LABEL] {key}")
        report.append({
            "type": "orphan_label",
            "item": str(key),
            "message": f"No matching image found for label '{key}'"
        })
        issues += 1

    for key, label_path in sorted(label_by_name.items()):
        if key not in image_keys:
            continue
        errors = check_label_file(label_path, args.classes)
        for error in errors:
            print(f"[INVALID] {label_path}: {error}")
            report.append({
                "type": "invalid_annotation",
                "item": str(label_path),
                "message": error
            })
            issues += 1

    print(f"\nImages: {len(images)}")
    print(f"Label files: {len(labels)}")
    print(f"Issues found: {issues}")
    report_path = root / "dataset_doctor_report.json"

    try:
        report_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )
    except OSError as exc:
        parser.exit(2, f"Error writing JSON report: {exc}\n")

    print(f"JSON report saved to: {report_path}")

    raise SystemExit(1 if issues else 0)


if __name__ == "__main__":
    main()
