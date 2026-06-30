"""
export_onnx.py — Export BanglaBERT Router to ONNX & Quantize
============================================================
Converts the fine-tuned PyTorch BanglaBERT model to ONNX format,
and applies INT8 dynamic quantization for faster inference on CPU.

Usage:
    python -m ml.export_onnx --model_id models/sentence_router_pt --output_dir models/sentence_router_onnx
"""

import os
import argparse
import subprocess

def export_and_quantize(model_id: str, output_dir: str):
    print(f"Exporting model from '{model_id}' to '{output_dir}' (ONNX)...")
    
    # Ensure optimum is installed
    try:
        import optimum
    except ImportError:
        print("Optimum not installed. Please run: pip install optimum[onnxruntime]")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Export to ONNX
    print("Running optimum-cli export...")
    export_cmd = [
        "optimum-cli", "export", "onnx", 
        "--model", model_id, 
        "--task", "text-classification",
        output_dir
    ]
    subprocess.run(export_cmd, check=True)
    print("Export complete.")
    
    # 2. Dynamic Quantization (INT8)
    # This reduces size by ~4x and speeds up CPU inference by ~2-3x
    print("Applying INT8 dynamic quantization...")
    quantize_cmd = [
        "optimum-cli", "onnxruntime", "quantize", 
        "--onnx_model", output_dir, 
        "--avx512", # optimizes for modern CPUs
        "-o", os.path.join(output_dir, "quantized")
    ]
    # We use dynamic quantization (default for onnxruntime quantize without calibration data)
    # The output will go to models/sentence_router_onnx/quantized
    subprocess.run(quantize_cmd, check=True)
    print("Quantization complete.")
    
    print(f"✅ Final quantized model is at: {os.path.join(output_dir, 'quantized')}")
    print("You can load it using ORTModelForSequenceClassification from optimum.onnxruntime.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_id", type=str, default="models/sentence_router_pt")
    parser.add_argument("--output_dir", type=str, default="models/sentence_router_onnx")
    args = parser.parse_args()
    
    export_and_quantize(args.model_id, args.output_dir)
