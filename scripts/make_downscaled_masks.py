import argparse, os
from PIL import Image

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--scales", nargs="+", type=int, required=True)
    args = ap.parse_args()

    in_dir = args.in_dir
    out_root = args.out_root

    files = [f for f in os.listdir(in_dir) if f.lower().endswith((".png",".jpg",".jpeg"))]
    files.sort()

    for s in args.scales:
        out_dir = os.path.join(out_root, f"masks_{s}")
        os.makedirs(out_dir, exist_ok=True)

        for f in files:
            p = os.path.join(in_dir, f)
            im = Image.open(p).convert("L")  # mask as grayscale
            w, h = im.size
            im2 = im.resize((max(1, w//s), max(1, h//s)), Image.NEAREST)
            im2.save(os.path.join(out_dir, os.path.splitext(f)[0] + ".png"))

        print("DONE:", out_dir, "(", len(files), "masks )")

if __name__ == "__main__":
    main()