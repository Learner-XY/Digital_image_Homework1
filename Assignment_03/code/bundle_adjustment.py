import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


def load_observations(data_dir):
    points2d = np.load(Path(data_dir) / "points2d.npz")
    view_ids = []
    point_ids = []
    xy_list = []
    for i, key in enumerate(sorted(points2d.files)):
        obs = points2d[key].astype(np.float32)
        visible = obs[:, 2] > 0.5
        ids = np.nonzero(visible)[0].astype(np.int64)
        view_ids.append(np.full(len(ids), i, dtype=np.int64))
        point_ids.append(ids)
        xy_list.append(obs[visible, :2])

    view_ids = np.concatenate(view_ids)
    point_ids = np.concatenate(point_ids)
    xy = np.concatenate(xy_list).astype(np.float32)

    first = points2d[sorted(points2d.files)[0]]
    n_views = len(points2d.files)
    n_points = first.shape[0]
    return view_ids, point_ids, xy, n_views, n_points, points2d


def init_points(points2d, n_points, f0=900.0, depth=3.0):
    xs = np.zeros(n_points, dtype=np.float32)
    ys = np.zeros(n_points, dtype=np.float32)
    counts = np.zeros(n_points, dtype=np.float32)
    for key in sorted(points2d.files):
        obs = points2d[key].astype(np.float32)
        visible = obs[:, 2] > 0.5
        xs[visible] += obs[visible, 0]
        ys[visible] += obs[visible, 1]
        counts[visible] += 1.0
    counts = np.maximum(counts, 1.0)
    mean_x = xs / counts
    mean_y = ys / counts

    pts = np.zeros((n_points, 3), dtype=np.float32)
    pts[:, 0] = (mean_x - 512.0) * depth / f0
    pts[:, 1] = -(mean_y - 512.0) * depth / f0
    pts[:, 2] = np.random.normal(0.0, 0.08, size=n_points).astype(np.float32)
    return pts


def euler_xyz_to_matrix(angles):
    x, y, z = angles[:, 0], angles[:, 1], angles[:, 2]
    cx, sx = torch.cos(x), torch.sin(x)
    cy, sy = torch.cos(y), torch.sin(y)
    cz, sz = torch.cos(z), torch.sin(z)

    ones = torch.ones_like(x)
    zeros = torch.zeros_like(x)
    rx = torch.stack(
        [
            ones,
            zeros,
            zeros,
            zeros,
            cx,
            -sx,
            zeros,
            sx,
            cx,
        ],
        dim=-1,
    ).reshape(-1, 3, 3)
    ry = torch.stack(
        [
            cy,
            zeros,
            sy,
            zeros,
            ones,
            zeros,
            -sy,
            zeros,
            cy,
        ],
        dim=-1,
    ).reshape(-1, 3, 3)
    rz = torch.stack(
        [
            cz,
            -sz,
            zeros,
            sz,
            cz,
            zeros,
            zeros,
            zeros,
            ones,
        ],
        dim=-1,
    ).reshape(-1, 3, 3)
    return rz @ ry @ rx


def project(points, eulers, trans, focal):
    rot = euler_xyz_to_matrix(eulers)
    pc = torch.bmm(rot, points.unsqueeze(-1)).squeeze(-1) + trans
    z = torch.clamp(pc[:, 2], max=-1e-3)
    u = -focal * pc[:, 0] / z + 512.0
    v = focal * pc[:, 1] / z + 512.0
    return torch.stack([u, v], dim=-1)


def save_obj(path, points, colors):
    colors = colors.astype(np.float32)
    if colors.max() > 1.0:
        colors = colors / 255.0
    with open(path, "w", encoding="utf-8") as f:
        for p, c in zip(points, colors):
            f.write(
                "v %.6f %.6f %.6f %.6f %.6f %.6f\n"
                % (p[0], p[1], p[2], c[0], c[1], c[2])
            )


def plot_outputs(out_dir, history, points, colors):
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 4))
    plt.plot([h["iter"] for h in history], [h["loss"] for h in history])
    plt.xlabel("iteration")
    plt.ylabel("MSE reprojection loss")
    plt.tight_layout()
    plt.savefig(out_dir / "loss_curve.png", dpi=180)
    plt.close()

    rng = np.random.default_rng(0)
    n = min(8000, len(points))
    idx = rng.choice(len(points), size=n, replace=False)
    c = colors[idx].astype(np.float32)
    if c.max() > 1.0:
        c = c / 255.0

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(points[idx, 0], points[idx, 1], points[idx, 2], c=c, s=1)
    ax.view_init(elev=8, azim=-80)
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(out_dir / "point_cloud_preview.png", dpi=180)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-dir", default="outputs/ba")
    parser.add_argument("--iters", type=int, default=800)
    parser.add_argument("--batch-size", type=int, default=65536)
    parser.add_argument("--sample-obs", type=int, default=200000)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--lr", type=float, default=1e-2)
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    view_np, point_np, xy_np, n_views, n_points, points2d = load_observations(args.data_dir)
    if args.sample_obs > 0 and args.sample_obs < len(xy_np):
        rng = np.random.default_rng(args.seed)
        keep = rng.choice(len(xy_np), size=args.sample_obs, replace=False)
        view_np, point_np, xy_np = view_np[keep], point_np[keep], xy_np[keep]

    f0 = 900.0
    init_pts = init_points(points2d, n_points, f0=f0)
    colors = np.load(Path(args.data_dir) / "points3d_colors.npy")

    view_ids = torch.as_tensor(view_np, dtype=torch.long, device=device)
    point_ids = torch.as_tensor(point_np, dtype=torch.long, device=device)
    xy = torch.as_tensor(xy_np, dtype=torch.float32, device=device)

    points = torch.nn.Parameter(torch.as_tensor(init_pts, dtype=torch.float32, device=device))
    eulers = torch.nn.Parameter(torch.zeros(n_views, 3, dtype=torch.float32, device=device))
    with torch.no_grad():
        eulers[:, 1] = torch.linspace(math.radians(-70), math.radians(70), n_views, device=device)
    trans = torch.nn.Parameter(torch.zeros(n_views, 3, dtype=torch.float32, device=device))
    with torch.no_grad():
        trans[:, 2] = -3.0
    raw_f = torch.nn.Parameter(torch.tensor(f0 - 100.0, device=device))

    optimizer = torch.optim.Adam(
        [
            {"params": [points], "lr": args.lr},
            {"params": [eulers, trans], "lr": args.lr * 0.4},
            {"params": [raw_f], "lr": args.lr * 0.05},
        ]
    )

    history = []
    n_obs = len(xy)
    for it in range(1, args.iters + 1):
        batch = torch.randint(0, n_obs, (min(args.batch_size, n_obs),), device=device)
        p = points[point_ids[batch]]
        cam = view_ids[batch]
        focal = torch.nn.functional.softplus(raw_f) + 100.0
        pred = project(p, eulers[cam], trans[cam], focal)
        diff = pred - xy[batch]
        loss = (diff * diff).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if it == 1 or it % 20 == 0 or it == args.iters:
            rmse = float(torch.sqrt(loss.detach()).cpu())
            record = {
                "iter": it,
                "loss": float(loss.detach().cpu()),
                "rmse": rmse,
                "focal": float(focal.detach().cpu()),
            }
            history.append(record)
            print(
                "iter=%04d loss=%.4f rmse=%.3f focal=%.2f"
                % (record["iter"], record["loss"], record["rmse"], record["focal"]),
                flush=True,
            )

    final_points = points.detach().cpu().numpy()
    save_obj(out_dir / "reconstructed_points.obj", final_points, colors)
    plot_outputs(out_dir, history, final_points, colors)

    with open(out_dir / "loss_history.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["iter", "loss", "rmse", "focal"])
        writer.writeheader()
        writer.writerows(history)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write("Bundle Adjustment simple PyTorch result\n")
        f.write(f"device: {device}\n")
        f.write(f"observations used: {n_obs}\n")
        f.write(f"points: {n_points}, views: {n_views}\n")
        f.write(f"final rmse: {history[-1]['rmse']:.4f}\n")
        f.write(f"final focal: {history[-1]['focal']:.4f}\n")


if __name__ == "__main__":
    main()
