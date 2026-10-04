"""캐릭터 스프라이트 시트 → 표정별 개별 PNG 분리.

game/assets/characters_sprite/<char>.png (투명 배경, 시트마다 배치가 다름)
  → game/assets/characters/<char>_<expr>.png

방법
1. 알파 마스크를 강하게 침식해 인물 몸통 '코어'만 남김 (머리카락 가닥으로 붙은 이웃 인물 분리)
2. 큰 코어 N개를 시드로 잡고 읽는 순서(위→아래, 왼→오)로 정렬
3. 마스크 위에서 watershed로 시드를 키워 모든 픽셀을 인물에 배정
4. 시드와 이어지지 않은 작은 조각(라벨 알약 등)은 제거
5. 같은 캐릭터의 모든 표정을 동일한 캔버스에 '바닥 정렬 + 몸통 중심 정렬'로 배치
   → 게임에서 표정을 바꿔도 크기·위치가 튀지 않음

  .venv\\Scripts\\python.exe tools\\split_sprites.py [--preview]
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "game" / "assets" / "characters_sprite"
DST = ROOT / "game" / "assets" / "characters"

# 시트별 표정 이름 (읽는 순서). 시트 이미지를 한 장씩 보고 정한 매핑.
SHEETS = {
    # 5+4, 라벨 있음: neutral / smile / sad / angry / surprised // cold / cry / shy / pin
    "yuri": ["neutral", "smile", "sad", "angry", "surprised", "cold", "cry", "shy", "pin"],
    # 5+4, 라벨: polite smile / forced smile / sad guilt / angry / surprised // cold / crying / embarrassed / wet
    "dohyun": ["neutral", "smile", "sad", "angry", "surprised", "cold", "cry", "shy", "wet"],
    # 3x3: 무표정 / 옅은 미소 / 눈 감은 슬픔 // 노려봄 / 놀람 / 냉담 // 울음 / 홍조 / USB
    "eunchae": ["neutral", "smile", "sad", "angry", "surprised", "cold", "cry", "shy", "usb"],
    # 3x3: 지루함 / 가짜 미소 / 공허 // 격노 / 움찔 / 경멸 // 이 악문 울음 / 어색함 / 손가락질
    "seungha": ["neutral", "smile", "sad", "angry", "surprised", "cold", "cry", "shy", "smirk"],
    # 3x3: 경계 / 작은 미소 / 슬픔 // 분노 / 놀람 / 노려봄 // 울음 / 당황 / 커터칼
    "haram": ["neutral", "smile", "sad", "angry", "surprised", "cold", "cry", "shy", "knife"],
    # 단일 전신
    "sion": ["neutral"],
    # 3년 전 해온: 왼쪽 전신 1 + 흉상 3x3 (무표정 / 눈 감은 웃음 / 시무룩 // 분노 / 놀람 / 씩 웃음 // 울음 / 쑥스러움 / 윙크 브이)
    "haeon": ["full", "neutral", "smile", "sad", "angry", "surprised", "grin", "cry", "shy", "peace"],
}
# 라벨 알약이 인물 아랫단에 겹쳐 그려진 시트 → 알약 윗선부터 아래를 잘라냄
LABEL_OVERLAP = {"dohyun"}
# 같은 캔버스로 맞추지 않을 항목 (구도가 다른 것)
SEPARATE_CANVAS = {("haeon", "full")}


def cores(mask, n):
    """침식 반경을 키워가며, 큰 코어 n개가 잡티와 확실히 갈리는(n번째가 n+1번째의 20배 이상) 첫 지점."""
    for r in range(3, 70, 3):
        er = nd.binary_erosion(mask, structure=np.ones((3, 3)), iterations=r)
        lab, k = nd.label(er)
        if k < n:
            continue
        sizes = nd.sum(er, lab, range(1, k + 1))
        order = np.argsort(-sizes)
        nth = sizes[order[n - 1]]
        nxt = sizes[order[n]] if k > n else 0
        if nth > 2000 and nth > 20 * nxt:
            return lab, [int(i) + 1 for i in order[:n]], r
    raise RuntimeError(f"cores: {n} not found")


def geodesic_grow(seeds, mask, max_iter=2000):
    """모든 시드를 마스크 안에서 동시에 1px씩 키움 → 실루엣을 따라 먼저 닿은 인물이 픽셀을 차지."""
    labels = seeds.copy()
    free = mask & (labels == 0)
    for _ in range(max_iter):
        grown = nd.grey_dilation(labels, size=(3, 3))
        claim = free & (grown > 0)
        if not claim.any():
            break
        labels[claim] = grown[claim]
        free &= ~claim
    return labels


def reading_order(centers):
    """(cy, cx) 목록을 행 단위로 묶어 위→아래, 왼→오 순서로."""
    idx = sorted(range(len(centers)), key=lambda i: centers[i][0])
    rows, cur = [], [idx[0]]
    for i in idx[1:]:
        if abs(centers[i][0] - np.mean([centers[j][0] for j in cur])) < 120:
            cur.append(i)
        else:
            rows.append(cur)
            cur = [i]
    rows.append(cur)
    return [i for row in rows for i in sorted(row, key=lambda j: centers[j][1])]


def split_sheet(name, names):
    rgba = np.array(Image.open(SRC / f"{name}.png").convert("RGBA"))
    alpha = rgba[..., 3]
    mask = alpha > 24
    mask = nd.binary_opening(mask, iterations=1)
    n = len(names)

    if n == 1:
        labels = np.where(mask, 1, 0)
        order = [1]
    else:
        lab, big, r = cores(mask, n)
        seeds = np.zeros(mask.shape, np.int32)
        for k, i in enumerate(big, 1):
            seeds[lab == i] = k
        labels = geodesic_grow(seeds, mask)
        # 시드에서 닿지 않은 조각: 큰 머리카락 조각만 가장 가까운 인물에 붙이고 나머지(라벨 알약 등)는 버림
        rest = mask & (labels == 0)
        comp, kc = nd.label(rest)
        if kc:
            _, (iy, ix) = nd.distance_transform_edt(labels == 0, return_indices=True)
            near = labels[iy, ix]
            dist = nd.distance_transform_edt(labels == 0)
            for c, sl in enumerate(nd.find_objects(comp), 1):
                part = comp[sl] == c
                h, w = part.shape
                pill = h < 70 and w > 90  # 라벨 알약 모양
                if part.sum() > 150 and not pill and dist[sl][part].min() < 25:
                    labels[sl][part] = np.bincount(near[sl][part]).argmax()
        centers = [nd.center_of_mass(seeds == k) for k in range(1, n + 1)]
        if name == "haeon":  # 전신(가장 큰 것)이 먼저, 나머지 흉상은 읽는 순서
            areas = [(labels == k).sum() for k in range(1, n + 1)]
            full = int(np.argmax(areas))
            rest = [i for i in reading_order(centers) if i != full]
            order = [full + 1] + [i + 1 for i in rest]
        else:
            order = [i + 1 for i in reading_order(centers)]
        print(f"  {name}: erosion r={r}, cores={n}")

    pieces = []
    for expr, k in zip(names, order):
        sel = labels == k
        # 경계 안티앨리어싱 살리기: 선택 영역을 1px 키운 범위의 원래 알파 사용
        keep = nd.binary_dilation(sel, iterations=1) & (alpha > 0)
        out = rgba.copy()
        out[..., 3] = np.where(keep, alpha, 0)
        out[~keep, :3] = 0
        ys, xs = np.nonzero(keep)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        crop = out[y0:y1, x0:x1]
        if name in LABEL_OVERLAP:
            crop = cut_label(crop)
        # 몸통 중심: 아래쪽 60% 영역의 열 무게중심 (머리카락 흩날림에 덜 흔들림)
        a = crop[..., 3] > 128
        lower = a[int(a.shape[0] * 0.4):]
        cx = nd.center_of_mass(lower)[1] if lower.any() else crop.shape[1] / 2
        pieces.append((expr, crop, cx))
    return pieces


def cut_label(crop):
    """아랫단 25%에서 알약 윗테두리(밝은 가로줄) 또는 알약 남색 면(가로로 길게 이어짐)이 처음 나오는 줄을 찾아 그 아래를 버림."""
    h = crop.shape[0]
    rgb, a = crop[..., :3].astype(int), crop[..., 3] > 128
    light = (rgb.min(-1) > 175) & a
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    navy = (b > r + 25) & (b > g + 15) & (b < 120) & (r < 60) & a

    def longest(row):
        run = best = 0
        for v in row:
            run = run + 1 if v else 0
            best = max(best, run)
        return best

    for y in range(int(h * 0.75), h):
        if longest(light[y]) >= 60 or longest(navy[y]) >= 110:
            crop = crop[: max(1, y - 2)].copy()
            ys = np.nonzero(crop[..., 3].any(1))[0]
            crop = crop[: ys.max() + 1]
            # 남은 테두리 잔선(밝은 픽셀 30개 이상인 마지막 줄들) 제거
            while crop.shape[0] > 10:
                last = crop[-1]
                if ((last[:, :3].min(-1) > 175) & (last[:, 3] > 128)).sum() < 30:
                    break
                crop = crop[:-1]
            return crop
    return crop


def normalize(name, pieces, pad=8):
    """같은 캐릭터 표정들을 하나의 캔버스 규격으로: 바닥 정렬 + 몸통 중심 정렬."""
    group = [p for p in pieces if (name, p[0]) not in SEPARATE_CANVAS]
    solo = [p for p in pieces if (name, p[0]) in SEPARATE_CANVAS]
    results = []
    if group:
        left = max(cx for _, c, cx in group)
        right = max(c.shape[1] - cx for _, c, cx in group)
        H = max(c.shape[0] for _, c, _ in group) + pad
        W = int(np.ceil(left + right)) + pad * 2
        for expr, c, cx in group:
            canvas = np.zeros((H, W, 4), np.uint8)
            x = int(round(pad + left - cx))
            y = H - c.shape[0]
            canvas[y:y + c.shape[0], x:x + c.shape[1]] = c
            results.append((expr, canvas))
    for expr, c, _ in solo:
        canvas = np.zeros((c.shape[0] + pad, c.shape[1] + pad * 2, 4), np.uint8)
        canvas[pad:, pad:pad + c.shape[1]] = c
        results.append((expr, canvas))
    return results


def preview(name, results, path):
    """분리 결과 확인용 콘택트 시트 (회색 체커 배경 + 파일명)."""
    from PIL import ImageDraw

    th = 360
    tiles = []
    for expr, arr in results:
        im = Image.fromarray(arr)
        im = im.resize((max(1, int(im.width * th / im.height)), th))
        bg = Image.new("RGBA", im.size, (70, 70, 78, 255))
        d = ImageDraw.Draw(bg)
        for yy in range(0, im.height, 20):
            for xx in range(0, im.width, 20):
                if (xx // 20 + yy // 20) % 2:
                    d.rectangle([xx, yy, xx + 19, yy + 19], fill=(90, 90, 100, 255))
        bg.alpha_composite(im)
        ImageDraw.Draw(bg).text((6, 6), f"{name}_{expr}", fill=(255, 220, 120, 255))
        tiles.append(bg)
    W = sum(t.width for t in tiles) + 6 * len(tiles)
    sheet = Image.new("RGBA", (W, th), (20, 20, 20, 255))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 6
    sheet.convert("RGB").save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default="", help="콘택트 시트를 저장할 폴더")
    ap.add_argument("only", nargs="*")
    args = ap.parse_args()
    DST.mkdir(parents=True, exist_ok=True)
    for name, names in SHEETS.items():
        if args.only and name not in args.only:
            continue
        if not (SRC / f"{name}.png").exists():
            print(f"skip {name} (no sheet)")
            continue
        results = normalize(name, split_sheet(name, names))
        for expr, arr in results:
            Image.fromarray(arr).save(DST / f"{name}_{expr}.png", optimize=True)
        print(f"{name}: {len(results)} → {', '.join(e for e, _ in results)}  canvas={results[0][1].shape[1]}x{results[0][1].shape[0]}")
        if args.preview:
            Path(args.preview).mkdir(parents=True, exist_ok=True)
            preview(name, results, Path(args.preview) / f"{name}.jpg")


if __name__ == "__main__":
    main()
