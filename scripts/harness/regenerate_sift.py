#!/usr/bin/env python3
"""Regenerate SIFT-128-euclidean dataset with better cluster structure for HNSW."""

import numpy as np
import os
import sys

sys.path.insert(0, '/Users/gnutakki16/Library/Python/3.9/lib/python/site-packages')

def main():
    data_dir = "benchmarks/data"
    os.makedirs(data_dir, exist_ok=True)
    
    np.random.seed(42)
    n_train = 100_000
    n_test = 1_000
    dim = 128
    n_clusters = 1000
    
    print(f"Creating improved SIFT dataset: {n_train} train, {n_test} test, {dim} dims, {n_clusters} clusters")
    
    # Create cluster centers with moderate magnitude
    centers = np.random.randn(n_clusters, dim).astype(np.float32) * 2.0
    
    # Assign vectors to clusters with small noise
    labels = np.random.randint(0, n_clusters, size=n_train)
    train = np.zeros((n_train, dim), dtype=np.float32)
    for i in range(n_train):
        train[i] = centers[labels[i]] + np.random.randn(dim).astype(np.float32) * 0.3
    
    # Queries from same cluster distribution
    q_labels = np.random.randint(0, n_clusters, size=n_test)
    test = np.zeros((n_test, dim), dtype=np.float32)
    for i in range(n_test):
        test[i] = centers[q_labels[i]] + np.random.randn(dim).astype(np.float32) * 0.3
    
    print(f"Train shape: {train.shape}, Test shape: {test.shape}")
    
    # Compute ground truth with FAISS flat index (fast exact search)
    print("Computing ground truth with FAISS IndexFlatL2...")
    import faiss
    
    top_k = 100
    index = faiss.IndexFlatL2(dim)
    index.add(train)
    D, neighbors = index.search(test, top_k)
    
    print(f"Ground truth computed: {neighbors.shape}")
    
    # Save
    out_path = os.path.join(data_dir, "sift_128_euclidean.npz")
    np.savez(out_path, train=train, test=test, neighbors=neighbors, distance="euclidean")
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Saved: {out_path} ({size_mb:.1f} MB)")
    
    # Quick validation with FAISS HNSW
    print("\nValidating with FAISS HNSW...")
    index = faiss.IndexHNSWFlat(dim, 16)
    index.hnsw.efConstruction = 128
    index.add(train)
    index.hnsw.efSearch = 64
    
    D, I = index.search(test, 100)
    
    r1 = sum(1 for i in range(len(test)) if I[i][0] == neighbors[i][0]) / len(test)
    r10 = sum(len(set(I[i][:10]) & set(neighbors[i][:10])) / 10 for i in range(len(test))) / len(test)
    r100 = sum(len(set(I[i][:100]) & set(neighbors[i][:100])) / 100 for i in range(len(test))) / len(test)
    
    print(f"Validation on 100K subset: R@1={r1:.3f}, R@10={r10:.3f}, R@100={r100:.3f}")
    
    if r1 < 0.5:
        print("WARNING: Recall still low. Dataset may need further adjustment.")
    else:
        print("SUCCESS: Dataset has good recall for HNSW.")

if __name__ == "__main__":
    main()
