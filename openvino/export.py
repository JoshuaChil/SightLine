"""
End-to-end Export + INT8 Quantization for YOLOv8 using OpenVINO + NNCF.

Features
- Optional export from a .pt checkpoint to OpenVINO IR (via ultralytics, if installed)
- Post-Training Quantization (INT8) using NNCF with images from a calibration folder
- Saves quantized IR next to the original IR

Usage (typical):
  python export.py --pt ../openvino/best.pt \
                   --ir-dir ./best_openvino_model \
                   --calib-dir ./calib_data \
                   --subset-size 200

If IR already exists in --ir-dir, export is skipped by default.
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
from typing import Callable, List, Tuple

import cv2
import numpy as np
import importlib
import openvino.runtime as ov


def _apply_openvino_nncf_compat_shim() -> None:
    """Expose runtime classes (Node, Model, etc.) on top-level 'openvino' for older/newer NNCF versions.

    Some NNCF builds expect symbols on the top-level openvino module (e.g., openvino.Node).
    This shim maps classes from openvino.runtime to openvino if they're missing.
    """
    try:
        ov_top = importlib.import_module("openvino")
        ov_rt = importlib.import_module("openvino.runtime")
    except Exception:
        return

    for name in ("Model", "Node", "PartialShape", "Shape", "Type", "Layout"):
        if not hasattr(ov_top, name) and hasattr(ov_rt, name):
            setattr(ov_top, name, getattr(ov_rt, name))


def find_ir(ir_dir: Path) -> Tuple[Path, Path]:
    xmls = sorted(ir_dir.glob("*.xml"))
    if not xmls:
        raise FileNotFoundError(f"No .xml found in {ir_dir}.")
    xml = xmls[0]
    bin_path = xml.with_suffix(".bin")
    if not bin_path.exists():
        raise FileNotFoundError(f"Weights file not found next to {xml}.")
    return xml, bin_path


def try_export_openvino_from_pt(pt_path: Path, out_dir: Path, imgsz: int = 640) -> None:
    """Export YOLOv8 .pt to OpenVINO IR using ultralytics if available.

    Skips if ultralytics is not installed; raises only on other unexpected errors.
    """
    if not pt_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {pt_path}")

    try:
        from ultralytics import YOLO  # type: ignore
    except Exception:
        # ultralytics not installed; simply skip export and rely on existing IR
        return

    import shutil

    out_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(pt_path))
    # This creates an OpenVINO IR somewhere under out_dir
    model.export(
        format="openvino",
        imgsz=imgsz,
        half=False,
        dynamic=False,
        int8=False,
        opset=12,
        project=str(out_dir),
        name="export",
    )

    # Find the first xml produced and copy next to out_dir for consistency
    produced = list(out_dir.rglob("*.xml"))
    if produced:
        src_xml = produced[0]
        src_bin = src_xml.with_suffix(".bin")
        dst_xml = out_dir / src_xml.name
        dst_bin = out_dir / src_bin.name
        if src_xml != dst_xml:
            shutil.copy2(src_xml, dst_xml)
        if src_bin.exists() and src_bin != dst_bin:
            shutil.copy2(src_bin, dst_bin)


def list_images(folder: Path) -> List[Path]:
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp")
    files: List[Path] = []
    for ext in exts:
        files.extend(Path(folder).glob(ext))
    files = sorted(f for f in files if f.is_file())
    if not files:
        raise FileNotFoundError(f"No images found in {folder} with {exts}.")
    return files


def letterbox(img: np.ndarray, new_shape: Tuple[int, int] = (640, 640), color=(114, 114, 114)) -> np.ndarray:
    h, w = img.shape[:2]
    r = min(new_shape[0] / h, new_shape[1] / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    img_resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((new_shape[0], new_shape[1], 3), color, dtype=img.dtype)
    top = (new_shape[0] - nh) // 2
    left = (new_shape[1] - nw) // 2
    canvas[top : top + nh, left : left + nw] = img_resized
    return canvas


def build_transform_fn(model: ov.Model, imgsz: int) -> Callable[[Path], np.ndarray | dict]:
    input_any_name = model.input(0).get_any_name() if hasattr(model.input(0), "get_any_name") else model.inputs[0].get_node().get_friendly_name()

    # Resolve model expected input shape (N, C, H, W)
    shape = list(model.input(0).shape)
    if len(shape) != 4:
        raise RuntimeError(f"Unexpected input shape for model: {shape}")
    _, c, h, w = shape
    h = int(h) if h is not None and h > 0 else imgsz
    w = int(w) if w is not None and w > 0 else imgsz

    def transform_fn(path: Path):
        img = cv2.imread(str(path))
        if img is None:
            raise FileNotFoundError(f"Failed to read image: {path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = letterbox(img, (h, w))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))  # HWC -> CHW
        img = np.expand_dims(img, 0)  # 1xCxHxW
        # Return dict for explicit mapping (robust for OpenVINO backend)
        return {input_any_name: img}

    return transform_fn


def quantize_ir(ir_xml: Path, calib_dir: Path, subset_size: int = 200, preset: str = "performance", out_suffix: str = "_INT8") -> Path:
    # Ensure NNCF <-> OpenVINO compatibility
    _apply_openvino_nncf_compat_shim()
    import nncf  # local import after shim

    core = ov.Core()
    model = core.read_model(str(ir_xml))

    # Prepare NNCF Dataset
    image_paths = list_images(calib_dir)
    transform_fn = build_transform_fn(model, imgsz=640)
    dataset = nncf.Dataset(image_paths, transform_fn)

    # Map preset string to enum if needed
    preset_map = {
        "performance": nncf.QuantizationPreset.PERFORMANCE,
        "mixed": nncf.QuantizationPreset.MIXED,
    }
    q_preset = preset_map.get(preset.lower(), nncf.QuantizationPreset.PERFORMANCE)

    # Quantize
    q_model = nncf.quantize(
        model,
        dataset,
        preset=q_preset,
        subset_size=max(1, subset_size),
        fast_bias_correction=True,
    )

    # Save quantized model next to the original
    out_xml = ir_xml.with_name(ir_xml.stem + out_suffix + ".xml")
    out_bin = out_xml.with_suffix(".bin")
    ov.serialize(q_model, str(out_xml), str(out_bin))
    return out_xml


def smoke_infer(ir_xml: Path, sample_image: Path | None = None) -> None:
    """Run a tiny inference to validate the model compiles and runs."""
    core = ov.Core()
    model = core.read_model(str(ir_xml))
    compiled = core.compile_model(model, "CPU")

    # Build input
    h, w = int(model.input(0).shape[2]), int(model.input(0).shape[3])
    if sample_image and Path(sample_image).exists():
        img = cv2.imread(str(sample_image))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = letterbox(img, (h, w))
        img = img.astype(np.float32) / 255.0
    else:
        img = np.full((h, w, 3), 0, np.float32)
    blob = np.transpose(img, (2, 0, 1))[None, ...]

    infer_req = compiled.create_infer_request()
    input_tensor_name = model.input(0).get_any_name() if hasattr(model.input(0), "get_any_name") else compiled.inputs[0].get_node().get_friendly_name()
    infer_req.set_tensor(input_tensor_name, ov.Tensor(array=blob))
    _ = infer_req.infer()


def main():
    parser = argparse.ArgumentParser(description="Export YOLOv8 to OpenVINO and quantize to INT8 with NNCF")
    parser.add_argument("--pt", type=str, default=str(Path(__file__).with_name("best.pt")), help="Path to YOLOv8 .pt checkpoint")
    parser.add_argument("--ir-dir", type=str, default=str(Path(__file__).with_name("best_openvino_model")), help="Directory to read/write OpenVINO IR")
    parser.add_argument("--calib-dir", type=str, default=str(Path(__file__).with_name("calib_data")), help="Calibration images directory")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size used for export")
    parser.add_argument("--subset-size", type=int, default=200, help="Number of calibration images to use")
    parser.add_argument("--preset", type=str, default="performance", choices=["performance", "mixed"], help="Quantization preset")
    parser.add_argument("--force-export", action="store_true", help="Force re-export IR from .pt if ultralytics is available")
    parser.add_argument("--smoke-test", action="store_true", help="Run a tiny inference after quantization")
    args = parser.parse_args()

    pt_path = Path(args.pt)
    ir_dir = Path(args.ir_dir)
    calib_dir = Path(args.calib_dir)
    ir_dir.mkdir(parents=True, exist_ok=True)

    # Export if needed
    need_export = args.force_export
    if not any(ir_dir.glob("*.xml")):
        need_export = True
    if need_export:
        try_export_openvino_from_pt(pt_path, ir_dir, imgsz=args.imgsz)

    # Load IR
    ir_xml, ir_bin = find_ir(ir_dir)
    print(f"Using IR: {ir_xml}")

    # Quantize
    out_xml = quantize_ir(ir_xml, calib_dir, subset_size=args.subset_size, preset=args.preset)
    print(f"Quantized model saved to: {out_xml}")

    # Optional smoke test
    if args.smoke_test:
        sample = None
        imgs = list_images(calib_dir)
        if imgs:
            sample = imgs[0]
        smoke_infer(out_xml, sample)
        print("Smoke inference completed.")


if __name__ == "__main__":
    main()

