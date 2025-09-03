import os
import time
import glob
import psutil
import cv2
import numpy as np
from ultralytics import YOLO
from tqdm import tqdm
import collections

# -----------------------------------------------------------------------------
# --- ⚙️ CONFIGURATION ---
# -----------------------------------------------------------------------------

# --- Model Paths ---
YOLO_MODEL_PATH = "best.pt"           # Path to your standard YOLOv8 .pt model

# --- Dataset ---
DATASET_PATH = "../Depth_Model/Indoor--1/test" # Path to the root of your test dataset
IMAGE_FOLDER = os.path.join(DATASET_PATH, "images")
LABEL_FOLDER = os.path.join(DATASET_PATH, "labels")

# --- Class Names ---
CLASS_NAMES = ['bed', 'chair', 'door', 'door-frame', 'shower', 'sink', 'sofa', 'stairs', 'table', 'toilet']

# --- Evaluation Parameters ---
IOU_THRESHOLD = 0.2     # IoU threshold for a detection to be a True Positive
CONF_THRESHOLD = 0.25   # Confidence threshold for post-processing

# -----------------------------------------------------------------------------
# ---  HELPER FUNCTIONS ---
# -----------------------------------------------------------------------------

def get_process_memory():
    """Returns the memory usage of the current process in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 ** 2

def load_ground_truth(label_path, img_width, img_height):
    """Loads ground truth bounding boxes from a YOLO format label file."""
    gts = []
    if not os.path.exists(label_path):
        return gts
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            class_id = int(parts[0])
            x_center, y_center, w, h = map(float, parts[1:])
            # Denormalize
            x1 = (x_center - w / 2) * img_width
            y1 = (y_center - h / 2) * img_height
            x2 = (x_center + w / 2) * img_width
            y2 = (y_center + h / 2) * img_height
            gts.append({'class_id': class_id, 'bbox': [x1, y1, x2, y2]})
    return gts

def calculate_iou(boxA, boxB):
    """Calculates Intersection over Union (IoU) between two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def calculate_ap(recall, precision):
    """Calculates Average Precision (AP) from recall and precision points."""
    mrec = np.concatenate(([0.], recall, [1.]))
    mpre = np.concatenate(([0.], precision, [0.]))
    
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
        
    i = np.where(mrec[1:] != mrec[:-1])[0]
    ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap

def evaluate_detections(all_gts, all_preds, num_classes):
    """Calculates Precision, Recall, F1, and mAP."""
    # Store detections and ground truths per class
    gts_by_class = collections.defaultdict(list)
    preds_by_class = collections.defaultdict(list)
    
    for i, gts in enumerate(all_gts):
        for gt in gts:
            gts_by_class[gt['class_id']].append({'image_idx': i, 'bbox': gt['bbox'], 'used': False})
            
    for i, preds in enumerate(all_preds):
        for pred in preds:
            preds_by_class[pred['class_id']].append({'image_idx': i, 'bbox': pred['bbox'], 'confidence': pred['confidence']})

    ap_per_class = []
    total_tp, total_fp, total_fn = 0, 0, 0

    for c in range(num_classes):
        # Sort predictions by confidence
        class_preds = sorted(preds_by_class[c], key=lambda x: x['confidence'], reverse=True)
        num_gts = len(gts_by_class[c])
        
        if num_gts == 0 and len(class_preds) == 0:
            continue
        
        tp = np.zeros(len(class_preds))
        fp = np.zeros(len(class_preds))

        for i, pred in enumerate(class_preds):
            pred_gts = [gt for gt in gts_by_class[c] if gt['image_idx'] == pred['image_idx']]
            
            best_iou = 0
            best_gt_idx = -1

            for j, gt in enumerate(pred_gts):
                iou = calculate_iou(pred['bbox'], gt['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = j

            if best_iou >= IOU_THRESHOLD:
                if not pred_gts[best_gt_idx]['used']:
                    tp[i] = 1
                    pred_gts[best_gt_idx]['used'] = True
                else:
                    fp[i] = 1
            else:
                fp[i] = 1

        # Calculate precision and recall
        fp_cumsum = np.cumsum(fp)
        tp_cumsum = np.cumsum(tp)
        
        recall = tp_cumsum / (num_gts + 1e-16)
        precision = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-16)
        
        # Calculate AP for this class
        ap = calculate_ap(recall, precision)
        ap_per_class.append(ap)
        
        # For overall Precision/Recall/F1, we use the last point (all detections)
        final_tp = int(np.sum(tp))
        final_fp = int(np.sum(fp))
        final_fn = num_gts - final_tp
        
        total_tp += final_tp
        total_fp += final_fp
        total_fn += final_fn

    # Calculate overall metrics
    mAP = np.mean(ap_per_class) if ap_per_class else 0.0
    overall_precision = total_tp / (total_tp + total_fp + 1e-16)
    overall_recall = total_tp / (total_tp + total_fn + 1e-16)
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall + 1e-16)

    return {
        "mAP": mAP,
        "Precision": overall_precision,
        "Recall": overall_recall,
        "F1-Score": overall_f1
    }

# -----------------------------------------------------------------------------
# --- MAIN EVALUATION SCRIPT ---
# -----------------------------------------------------------------------------
def main():
    print("Starting YOLO model evaluation...")
    
    image_paths = sorted(glob.glob(os.path.join(IMAGE_FOLDER, "*")))
    if not image_paths:
        print(f"Error: No images found in {IMAGE_FOLDER}")
        return

    all_gts = []
    for img_path in image_paths:
        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        label_name = os.path.splitext(os.path.basename(img_path))[0] + ".txt"
        label_path = os.path.join(LABEL_FOLDER, label_name)
        all_gts.append(load_ground_truth(label_path, w, h))

    # --- Evaluate Standard YOLOv8 Model ---
    print("\n" + "="*50)
    print("🔬 EVALUATING: Standard YOLOv8 (.pt)")
    print("="*50)
    
    mem_before = get_process_memory()
    model_yolo = YOLO(YOLO_MODEL_PATH)
    model_yolo.to("cpu")
    mem_after = get_process_memory()
    
    all_preds_yolo = []
    
    # Warm-up run
    _ = model_yolo(image_paths[0], verbose=False)
    
    start_time = time.time()
    for img_path in tqdm(image_paths, desc="YOLOv8 Inference"):
        res = model_yolo(img_path, verbose=False)[0]
        preds = []
        for box in res.boxes:
            preds.append({
                'bbox': box.xyxy[0].tolist(),
                'confidence': float(box.conf[0]),
                'class_id': int(box.cls[0])
            })
        all_preds_yolo.append(preds)
    end_time = time.time()
    
    total_time_yolo = end_time - start_time
    avg_latency_yolo = (total_time_yolo / len(image_paths)) * 1000  # in ms
    fps_yolo = len(image_paths) / total_time_yolo
    
    metrics_yolo = evaluate_detections(all_gts, all_preds_yolo, len(CLASS_NAMES))
    
    results = {
        "Disk Size (MB)": os.path.getsize(YOLO_MODEL_PATH) / (1024**2),
        "RAM Usage (MB)": mem_after - mem_before,
        "Latency (ms)": avg_latency_yolo,
        "FPS": fps_yolo,
        **metrics_yolo
    }
    
    # --- Print Results ---
    print("\n" + "="*50)
    print("📊 YOLO EVALUATION RESULTS")
    print("="*50)
    
    print(f"Disk Size (MB): {results['Disk Size (MB)']:.2f}")
    print(f"RAM Usage (MB): {results['RAM Usage (MB)']:.2f}")
    print(f"Latency (ms/img): {results['Latency (ms)']:.2f}")
    print(f"Throughput (FPS): {results['FPS']:.2f}")
    print(f"mAP @50: {results['mAP']:.4f}")
    print(f"F1-Score: {results['F1-Score']:.4f}")
    print(f"Precision: {results['Precision']:.4f}")
    print(f"Recall: {results['Recall']:.4f}")
    print("="*50)

if __name__ == "__main__":
    main()
