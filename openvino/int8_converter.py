import openvino as ov
import numpy as np
import cv2
from pathlib import Path
from typing import List, Tuple
import json

# Configuration
INPUT_MODEL_PATH = "best.onnx"
OUTPUT_MODEL_PATH = "optimized2_int8"
CALIBRATION_DATASET_PATH = "calib3"
INPUT_SIZE = (640, 640)


def preprocess_image(image_path: str, input_size: Tuple[int, int] = (640, 640)) -> np.ndarray:
    """Preprocess image for YOLOv8 inference"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
        
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize while maintaining aspect ratio
    h, w = image.shape[:2]
    scale = min(input_size[0] / h, input_size[1] / w)
    new_h, new_w = int(h * scale), int(w * scale)
    
    resized = cv2.resize(image, (new_w, new_h))
    
    # Pad to target size
    pad_h = (input_size[0] - new_h) // 2
    pad_w = (input_size[1] - new_w) // 2
    
    padded = np.pad(resized, 
                   ((pad_h, input_size[0] - new_h - pad_h),
                    (pad_w, input_size[1] - new_w - pad_w),
                    (0, 0)), 
                   mode='constant', constant_values=114)
    
    # Normalize to [0, 1] and transpose to NCHW format
    normalized = padded.astype(np.float32) / 255.0
    transposed = np.transpose(normalized, (2, 0, 1))  # HWC to CHW
    
    return np.expand_dims(transposed, axis=0)


def create_calibration_data_simple(dataset_path: str, num_samples: int = 500):
    """Create calibration dataset and save as numpy arrays"""
    dataset_path = Path(dataset_path)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(dataset_path.glob(f'**/*{ext}')))
        image_files.extend(list(dataset_path.glob(f'**/*{ext.upper()}')))
    
    image_files = image_files[:num_samples]
    print(f"Found {len(image_files)} images for calibration")
    
    calibration_data = []
    for i, img_path in enumerate(image_files):
        try:
            preprocessed = preprocess_image(str(img_path), INPUT_SIZE)
            calibration_data.append(preprocessed)
            
            if (i + 1) % 25 == 0:
                print(f"Processed {i + 1}/{len(image_files)} images")
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue
    
    # Save calibration data
    calib_dir = Path("calibration_data")
    calib_dir.mkdir(exist_ok=True)
    
    for i, data in enumerate(calibration_data):
        np.save(calib_dir / f"sample_{i:04d}.npy", data)
    
    print(f"Saved {len(calibration_data)} calibration samples to {calib_dir}")
    return calib_dir


def quantize_with_pot_config():
    """
    Create POT configuration file for quantization
    """
    config = {
        "model": {
            "model_name": "yolov8",
            "model": INPUT_MODEL_PATH,
            "weights": INPUT_MODEL_PATH.replace('.onnx', '.bin') if INPUT_MODEL_PATH.endswith('.onnx') else None
        },
        "engine": {
            "type": "simplified",
            "data_source": "calibration_data"
        },
        "compression": {
            "algorithms": [
                {
                    "name": "DefaultQuantization",
                    "params": {
                        "target_device": "CPU",
                        "preset": "performance",
                        "stat_subset_size": 300
                    }
                }
            ]
        }
    }
    
    # Remove weights field if not applicable
    if config["model"]["weights"] is None:
        del config["model"]["weights"]
    
    # Save config
    with open("pot_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("POT configuration saved as pot_config.json")
    return "pot_config.json"


def quantize_with_openvino_api(input_model_path: str, output_model_path: str, 
                              calibration_data_dir: Path):
    """
    Quantize using OpenVINO Python API with simple approach
    """
    
    # Load model
    core = ov.Core()
    model = core.read_model(input_model_path)
    
    print(f"Original model precision: {model.get_rt_info()}")
    
    # Compile model for CPU to get baseline
    compiled_model = core.compile_model(model, "CPU")
    
    # Get calibration data
    calib_files = list(calibration_data_dir.glob("*.npy"))
    print(f"Using {len(calib_files)} calibration samples")
    
    # Simple quantization using OpenVINO's built-in method
    # Note: This is a simplified approach, results may vary
    
    try:
        # Try to use OpenVINO's quantization if available
        from openvino.tools.pot import optimize
        
        # Load calibration dataset
        calibration_dataset = []
        input_name = model.input().any_name
        
        for calib_file in calib_files[:500]:  # Limit to 100 samples
            data = np.load(calib_file)
            calibration_dataset.append({input_name: data})
        
        # Create dataset for POT
        def data_loader():
            for sample in calibration_dataset:
                yield sample
        
        # Quantize (this is a placeholder - actual POT API may differ)
        print("Attempting quantization...")
        
        # Alternative: Save model and use command line POT
        temp_ir_path = "temp_model.xml"
        ov.save_model(model, temp_ir_path)
        
        print(f"Model converted to IR format: {temp_ir_path}")
        print("For INT8 quantization, use OpenVINO's POT tool:")
        print(f"pot -c pot_config.json -m {temp_ir_path} -o {output_model_path}")
        
        return temp_ir_path
        
    except ImportError:
        print("POT not available in this OpenVINO version")
        print("Saving as FP32 OpenVINO IR model instead...")
        
        # Save as OpenVINO IR (FP32)
        ov.save_model(model, output_model_path + ".xml")
        print(f"Model saved as: {output_model_path}.xml")
        
        return output_model_path + ".xml"


def manual_quantization_approach(input_model_path: str, output_model_path: str):
    """
    Manual approach using OpenVINO Model Optimizer
    """
    
    try:
        # Import Model Optimizer
        from openvino.tools import mo
        
        print("Converting with Model Optimizer...")
        
        # Convert ONNX to OpenVINO IR with compression
        ov_model = mo.convert_model(
            input_model=input_model_path,
            compress_to_fp16=True,  # At least reduce to FP16
        )
        
        # Save model
        ov.save_model(ov_model, output_model_path)
        print(f"Model converted and saved to: {output_model_path}")
        
        return ov_model
        
    except Exception as e:
        print(f"Model Optimizer approach failed: {e}")
        return None


def main():
    """Main quantization workflow"""
    
    try:
        print("Starting YOLOv8 quantization workflow...")
        print(f"OpenVINO version: {ov.__version__}")
        
        # Step 1: Create calibration data
        print("\nStep 1: Creating calibration data...")
        calib_dir = create_calibration_data_simple(CALIBRATION_DATASET_PATH, num_samples=500)
        
        # Step 2: Create POT config
        print("\nStep 2: Creating POT configuration...")
        config_file = quantize_with_pot_config()
        
        # Step 3: Try quantization
        print("\nStep 3: Attempting quantization...")
        
        # Method 1: OpenVINO API
        result = quantize_with_openvino_api(INPUT_MODEL_PATH, OUTPUT_MODEL_PATH, calib_dir)
        
        if result is None:
            # Method 2: Manual approach
            print("\nTrying manual quantization...")
            result = manual_quantization_approach(INPUT_MODEL_PATH, OUTPUT_MODEL_PATH)
        
        if result:
            print("\nQuantization workflow completed!")
            print("\nNext steps:")
            print("1. If you have OpenVINO POT installed, run:")
            print(f"   pot -c pot_config.json -m {result} -o {OUTPUT_MODEL_PATH}_int8")
            print("2. Or use the converted FP32/FP16 model directly")
            print("3. Test the quantized model for accuracy")
        
    except Exception as e:
        print(f"Error in quantization workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


# Command-line POT instructions
def print_pot_instructions():
    """Print instructions for using POT command line tool"""
    
    instructions = """
    
# If POT (Post-Training Optimization Tool) is available, use these commands:

# 1. First, convert ONNX to OpenVINO IR:
mo --input_model yolov8n.onnx --output_dir ./

# 2. Create calibration dataset (done by script above)

# 3. Run POT quantization:
pot -c pot_config.json -m yolov8n.xml -o yolov8n_int8

# Alternative: Use benchmark_app for performance testing:
benchmark_app -m yolov8n.xml -d CPU
benchmark_app -m yolov8n_int8.xml -d CPU

# Compare the performance results!
    """
    
    print(instructions)