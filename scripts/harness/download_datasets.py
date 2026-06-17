#!/usr/bin/env python3
"""
Download ANN-Benchmarks datasets for the Almanac benchmark harness.

Downloads SIFT1M and GloVe-100 from standard sources and converts
to numpy .npz format for use by scripts/harness/benchmark_harness.py.

Usage:
    python3 scripts/harness/download_datasets.py

Sources:
    - SIFT: http://corpus-texmex.irisa.fr/ (sift.tar.gz)
    - GloVe: https://nlp.stanford.edu/data/glove.6B.zip (preprocessed to 100d)
"""

import os
import sys
import struct
import urllib.request
import tarfile
import zipfile
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "benchmarks", "data")


def download_file(url: str, dest: str) -> str:
    """Download a file with progress reporting."""
    if os.path.exists(dest):
        print(f"  Already exists: {dest}")
        return dest

    print(f"  Downloading {url} -> {dest}")
    print(f"  (This may take a few minutes for large datasets)")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 / total_size)
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r    {mb:.1f}/{total_mb:.1f} MB ({pct:.1f}%)")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, reporthook)
    print()  # newline after progress
    return dest


def read_fvecs(path: str) -> np.ndarray:
    """Read .fvecs format (TEXMEX feature vectors)."""
    with open(path, "rb") as f:
        data = f.read()
    
    # First 4 bytes = dimension
    dim = struct.unpack("i", data[:4])[0]
    
    # Each vector is 4 bytes dim + dim * 4 bytes floats
    vec_size = 4 + dim * 4
    n_vectors = len(data) // vec_size
    
    vectors = np.zeros((n_vectors, dim), dtype=np.float32)
    for i in range(n_vectors):
        offset = i * vec_size
        # Skip the dimension prefix (already known)
        vectors[i] = struct.unpack(f"{dim}f", data[offset + 4:offset + vec_size])
    
    return vectors


def read_ivecs(path: str) -> np.ndarray:
    """Read .ivecs format (TEXMEX integer vectors / ground truth)."""
    with open(path, "rb") as f:
        data = f.read()
    
    dim = struct.unpack("i", data[:4])[0]
    vec_size = 4 + dim * 4
    n_vectors = len(data) // vec_size
    
    vectors = np.zeros((n_vectors, dim), dtype=np.int32)
    for i in range(n_vectors):
        offset = i * vec_size
        vectors[i] = struct.unpack(f"{dim}i", data[offset + 4:offset + vec_size])
    
    return vectors


def download_sift():
    """Download and convert SIFT1M dataset."""
    print("\n[1/2] SIFT-128-euclidean (1M vectors, 128 dims)")
    
    url = "http://corpus-texmex.irisa.fr/sift.tar.gz"
    tar_path = os.path.join(DATA_DIR, "sift.tar.gz")
    
    download_file(url, tar_path)
    
    # Extract
    extract_dir = os.path.join(DATA_DIR, "sift")
    if not os.path.exists(extract_dir):
        print(f"  Extracting {tar_path}...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(DATA_DIR)
    
    # Read and convert
    base_path = os.path.join(extract_dir, "sift_base.fvecs")
    query_path = os.path.join(extract_dir, "sift_query.fvecs")
    gt_path = os.path.join(extract_dir, "sift_groundtruth.ivecs")
    
    print(f"  Reading base vectors...")
    base = read_fvecs(base_path)
    print(f"    Base: {base.shape}")
    
    print(f"  Reading query vectors...")
    queries = read_fvecs(query_path)
    print(f"    Queries: {queries.shape}")
    
    print(f"  Reading ground truth...")
    gt = read_ivecs(gt_path)
    print(f"    Ground truth: {gt.shape}")
    
    # Save as npz
    out_path = os.path.join(DATA_DIR, "sift_128_euclidean.npz")
    np.savez(out_path, train=base, test=queries, neighbors=gt, distance="euclidean")
    print(f"  Saved to {out_path}")
    
    return out_path


def download_glove():
    """Download and convert GloVe-100 dataset."""
    print("\n[2/2] GloVe-100-angular (1.2M vectors, 100 dims)")
    
    # Download glove.6B zip (contains 50d, 100d, 200d, 300d)
    url = "https://nlp.stanford.edu/data/glove.6B.zip"
    zip_path = os.path.join(DATA_DIR, "glove.6B.zip")
    
    download_file(url, zip_path)
    
    # Extract
    extract_dir = os.path.join(DATA_DIR, "glove.6B")
    if not os.path.exists(extract_dir):
        print(f"  Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
    
    # Read 100d file
    txt_path = os.path.join(extract_dir, "glove.6B.100d.txt")
    print(f"  Reading word vectors from {txt_path}...")
    
    vectors = []
    words = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            parts = line.strip().split()
            word = parts[0]
            vec = [float(x) for x in parts[1:]]
            vectors.append(vec)
            words.append(word)
            if (i + 1) % 50000 == 0:
                print(f"    Read {i+1} vectors...")
    
    vectors = np.array(vectors, dtype=np.float32)
    print(f"  Total vectors: {vectors.shape}")
    
    # For ANN benchmarks, we use all vectors as the base and sample queries
    # Standard: use first 100K as queries, rest as base (or specific split)
    # Actually, glove-100-angular in ann-benchmarks uses 1,183,514 train and 10,000 test
    # Let's follow that: first 10K as test, rest as train
    n_test = 10000
    test = vectors[:n_test]
    train = vectors[n_test:]
    
    print(f"  Train: {train.shape}, Test: {test.shape}")
    
    # Compute ground truth with brute force (cosine similarity = 1 - cosine distance)
    # For angular distance, nearest neighbors by cosine similarity
    print(f"  Computing ground truth (brute force cosine similarity)...")
    print(f"  This will take a few minutes...")
    
    # Normalize for cosine similarity
    train_norm = train / np.linalg.norm(train, axis=1, keepdims=True)
    test_norm = test / np.linalg.norm(test, axis=1, keepdims=True)
    
    # Compute similarities (can be slow for 1.1M x 10K)
    # Use batching to avoid memory issues
    batch_size = 1000
    top_k = 100
    neighbors = np.zeros((n_test, top_k), dtype=np.int32)
    
    for i in range(0, n_test, batch_size):
        end = min(i + batch_size, n_test)
        batch = test_norm[i:end]
        sims = batch @ train_norm.T  # (batch, train)
        # Get top-k indices (highest similarity = nearest neighbors)
        top_k_idx = np.argpartition(-sims, top_k, axis=1)[:, :top_k]
        # Sort within top-k
        for j in range(end - i):
            idx = top_k_idx[j]
            sorted_idx = idx[np.argsort(-sims[j, idx])]
            neighbors[i + j] = sorted_idx
        print(f"    Processed {end}/{n_test} queries...")
    
    # Save as npz
    out_path = os.path.join(DATA_DIR, "glove_100_angular.npz")
    np.savez(out_path, train=train, test=test, neighbors=neighbors, distance="angular")
    print(f"  Saved to {out_path}")
    
    return out_path


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")
    
    try:
        download_sift()
    except Exception as e:
        print(f"SIFT download failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        download_glove()
    except Exception as e:
        print(f"GloVe download failed: {e}")
        import traceback
        traceback.print_exc()
    
    # List files
    print(f"\nData directory contents:")
    for f in sorted(os.listdir(DATA_DIR)):
        path = os.path.join(DATA_DIR, f)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  {f}: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
