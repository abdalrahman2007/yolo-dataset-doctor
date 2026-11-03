import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from doctor import check_label_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCTOR_SCRIPT = PROJECT_ROOT / "doctor.py"


class TestLabelValidation(unittest.TestCase):
    def check_text(self, content, num_classes=22):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "label.txt"
            path.write_text(content, encoding="utf-8")
            return check_label_file(path, num_classes)

    def test_valid_annotation(self):
        self.assertEqual(
            self.check_text("0 0.5 0.5 0.2 0.2\n"),
            [],
        )
        
    def test_box_exceeds_right_boundary(self):
        errors = self.check_text("0 0.90 0.5 0.30 0.2\n")
        self.assertTrue(any("outside image boundaries" in e for e in errors))

    def test_box_exceeds_left_boundary(self):
        errors = self.check_text("0 0.10 0.5 0.30 0.2\n")
        self.assertTrue(any("outside image boundaries" in e for e in errors))

    def test_box_exceeds_bottom_boundary(self):
        errors = self.check_text("0 0.5 0.90 0.2 0.30\n")
        self.assertTrue(any("outside image boundaries" in e for e in errors))

    def test_box_exceeds_top_boundary(self):
        errors = self.check_text("0 0.5 0.10 0.2 0.30\n")
        self.assertTrue(any("outside image boundaries" in e for e in errors))

    def test_box_touching_image_boundaries_is_valid(self):
        errors = self.check_text("0 0.5 0.5 1.0 1.0\n")
        self.assertEqual(errors, [])

    def test_out_of_range_class(self):
        errors = self.check_text("22 0.5 0.5 0.2 0.2\n")
        self.assertTrue(any("class ID 22" in e for e in errors))

    def test_invalid_coordinate(self):
        errors = self.check_text("0 1.5 0.5 0.2 0.2\n")
        self.assertTrue(any("x_center" in e for e in errors))

    def test_non_finite_value(self):
        errors = self.check_text("0 nan 0.5 0.2 0.2\n")
        self.assertTrue(any("finite" in e for e in errors))

    def test_zero_width(self):
        errors = self.check_text("0 0.5 0.5 0 0.2\n")
        self.assertTrue(any("positive" in e for e in errors))

    def test_wrong_number_of_values(self):
        errors = self.check_text("0 0.5 0.5\n")
        self.assertTrue(any("expected 5 values" in e for e in errors))

    def test_empty_label_file_is_valid(self):
        self.assertEqual(self.check_text(" \n\n"), [])


class TestDatasetCLI(unittest.TestCase):
    
    def test_clean_dataset_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            images = root / "images"
            labels = root / "labels"
            images.mkdir()
            labels.mkdir()

            (images / "cat.jpg").touch()
            (labels / "cat.txt").write_text(
                "0 0.5 0.5 0.2 0.2\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(DOCTOR_SCRIPT),
                    str(root),
                    "--classes",
                    "1",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Issues found: 0", result.stdout)

    def test_invalid_class_count_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(DOCTOR_SCRIPT),
                    tmp,
                    "--classes",
                    "0",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            self.assertEqual(result.returncode, 2)

    


if __name__ == "__main__":
    unittest.main()
