import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
from PIL import Image
import imagehash
import glob
from pathlib import Path

def load_image(path, size=None):
    # 1. Read in BGR color
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"couldn’t open {path}")
    # 2. Optionally resize to a fixed resolution
    if size is not None:
        img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    # 3. Convert to RGB if you prefer that order
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
import os
import sys

def list_images_recursively(folder, exts=('.jpg','.jpeg','.png','.bmp','.tif')):
    img_paths = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(exts):
                img_paths.append(os.path.join(root, f))
    return sorted(img_paths)

def choose_reference(paths):
    if not paths:
        print("No images found under that folder.")
        sys.exit(1)
    print("Found these images:")
    for i, p in enumerate(paths):
        # print a shorter, relative path for clarity
        print(f"  [{i}] {os.path.relpath(p)}")
    idx = input(f"Enter the index of your reference image [0–{len(paths)-1}]: ")
    try:
        idx = int(idx)
        return paths[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)

def compute_phash(path, hash_size=8, highfreq_factor=4):
    return imagehash.phash(Image.open(path), hash_size=hash_size, highfreq_factor=highfreq_factor)


def get_most_different(ref_path, base_folder, top_n=5):
    """
    Compare every image under `base_folder` to `ref_path` using pHash,
    and return the top_n most different as a list of (distance, path).
    """
    # 1. Precompute the reference hash
    ref_hash = compute_phash(ref_path)

    # 2. Gather all images and filter out the reference itself
    all_imgs = list_images_recursively(base_folder)
    others   = [p for p in all_imgs if os.path.normpath(p) != os.path.normpath(ref_path)]

    # 3. Compute distances
    results = []
    for p in others:
        h = compute_phash(p)
        dist = ref_hash - h  # Hamming distance
        results.append((dist, p))

    # 4. Sort descending: largest distance = most different
    results.sort(key=lambda x: x[0], reverse=True)

    # 5. Return the top_n entries
    return results[:top_n]

def cluster_by_phash(folder, threshold=10, hash_size=8, highfreq_factor=4):
    """
    Walk `folder`, compute pHash for each image, then form clusters:
     - Pick the first unclustered image as a seed
     - All images within `threshold` Hamming distance join its cluster
     - Remove them and repeat until none remain.
    Returns a list of clusters, each a list of file-paths.
    """
    paths = list_images_recursively(folder)
    hashes = {p: compute_phash(p, hash_size) for p in paths}
    unclustered = sorted(set(paths))
    clusters = []

    while unclustered:
        seed = unclustered.pop()
        seed_hash = hashes[seed]
        cluster = [seed]

        # compare to everything else
        for other in list(unclustered):
            if (seed_hash - hashes[other]) <= threshold:
                cluster.append(other)
                unclustered.remove(other)

        clusters.append(cluster)

    return clusters

def cluster_representatives(clusters, hashes):
    """
    For each cluster (a list of paths), pick the medoid:
    the path whose sum of Hamming distances to all others is smallest.
    `hashes` is a dict: path → ImageHash
    """
    reps = []
    for cluster in clusters:
        # compute total distance for each candidate
        total_dists = []
        for p in cluster:
            dist = sum((hashes[p] - hashes[q]) for q in cluster)
            total_dists.append((dist, p))
        # pick the path with minimal total distance
        _, medoid = min(total_dists, key=lambda x: x[0])
        reps.append(medoid)
    return reps

# def run_phash_clustering(
#     base_folder: str,
#     hash_size: int = 16,
#     highfreq_factor: int = 4,
#     threshold: int = 1,
#     output_dir: str = "output/comparewithphash"
# ):
#     """
#     1) Cluster images under base_folder by pHash similarity
#     2) Pick one medoid rep per cluster
#     3) Sort clusters by size (desc)
#     4) Print a summary
#     5) Save the summary to a text file in output_dir
#     Returns:
#         List of (cluster_list, representative_path) tuples, sorted by cluster size desc.
#     """
#     # 1) Build clusters
#     clusters = cluster_by_phash(
#         folder=base_folder,
#         threshold=threshold,
#         hash_size=hash_size,
#         highfreq_factor=highfreq_factor
#     )

#     # 2) Compute hashes for medoid selection
#     #    (only once per image)
#     hashes = {
#         p: compute_phash(p, hash_size, highfreq_factor)
#         for cluster in clusters for p in cluster
#     }

#     # 3) Pick one representative per cluster
#     reps = cluster_representatives(clusters, hashes)

#     # 4) Pair & sort clusters by size (largest first)
#     paired = list(zip(clusters, reps))
#     paired.sort(key=lambda x: len(x[0]), reverse=True)

#     # 5) Print summary to console
#     print(f"Found {len(paired)} clusters; returning {len(paired)} representatives:")
#     for i, (cluster, rep) in enumerate(paired, start=1):
#         print(f" Group {i:02d} ({len(cluster):2d} images): {rep}")

#     # 6) Write results to file
#     out_path = Path(output_dir)
#     out_path.mkdir(parents=True, exist_ok=True)
#     fname = f"hashsize_{hash_size}_threshold_{threshold}.txt"
#     file_path = out_path / fname

#     with file_path.open("w", encoding="utf-8") as f:
#         f.write(f"Found {len(paired)} clusters; returning {len(paired)} representatives\n\n")
#         for i, (cluster, rep) in enumerate(paired, start=1):
#             f.write(f"Group {i:02d} ({len(cluster):2d} images): {rep}\n")

#     print(f"\nResults saved to {file_path.resolve()}")
#     return paired

def run_multiple_rounds(
    base_folder: str,
    hash_size: int,
    highfreq_factor: int,
    threshold: int,
    num_rounds: int = 1,
    output_dir: str = "output/comparewithphash"
):
    """
    Runs clustering `num_rounds` times with the same parameters,
    writes one file per round and a summary file indicating
    whether all rounds produced identical representatives.
    Returns a list of rep‐lists for each round.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    all_reps = []
    for rnd in range(1, num_rounds + 1):
        # 1) cluster
        clusters = cluster_by_phash(
            folder=base_folder,
            threshold=threshold,
            hash_size=hash_size,
            highfreq_factor=highfreq_factor
        )
        # 2) compute hashes for medoid selection
        hashes = {
            p: compute_phash(p, hash_size, highfreq_factor)
            for cluster in clusters for p in cluster
        }
        # 3) pick reps
        reps = cluster_representatives(clusters, hashes)
        all_reps.append(reps)

        # 4) write round file
        fname = (
            f"hs{hash_size}_hf{highfreq_factor}_thr{threshold}"
            # f"_round{rnd}.txt"
            f".txt"
        )
        with (out_path / fname).open("w", encoding="utf-8") as f:
            f.write(f"Round {rnd}: {len(clusters)} clusters, {len(reps)} reps\n\n")
            for i, (cluster, rep) in enumerate(reps, start=1):
                f.write(f"Group {i:02d} ({len(cluster):2d} images): {rep}\n")

    # 5) compare all rounds
    # baseline = all_reps[0]
    # diffs = [i+1 for i, reps in enumerate(all_reps) if reps != baseline]

    # # 6) write summary
    # summary_name = (
    #     f"hs{hash_size}_hf{highfreq_factor}_thr{threshold}_summary.txt"
    # )
    # with (out_path / summary_name).open("w", encoding="utf-8") as f:
    #     if len(diffs) == 0:
    #         f.write(
    #             f"hash_size={hash_size}, highfreq_factor={highfreq_factor}, "
    #             f"threshold={threshold} → all {num_rounds} rounds produce identical reps.\n"
    #         )
    #     else:
    #         f.write(
    #             f"hash_size={hash_size}, highfreq_factor={highfreq_factor}, "
    #             f"threshold={threshold} → rounds differ in: {diffs}\n"
    #         )

    # print(f"Done: results in `{output_dir}`")
    return all_reps



if __name__ == "__main__":
    base_folder = r"T:\jwst\static\img\full-size\epoch1\lw"
    hash_sizes       = [8, 16, 32]
    highfreq_factors = [2, 4]
    thresholds       = [0, 1, 5, 10, 15, 20]
    num_rounds       = 3
    output_dir       = "output/comparewithphash"

    # ← Your for-loops over all parameter combinations:
    for hs in hash_sizes:
        for hf in highfreq_factors:
            for thr in thresholds:
                print(f"\n>> Testing hs={hs}, hf={hf}, thr={thr}")
                run_multiple_rounds(
                    base_folder=base_folder,
                    hash_size=hs,
                    highfreq_factor=hf,
                    threshold=thr,
                    num_rounds=num_rounds,
                    output_dir=output_dir
                )

    print("\nAll combinations done.")