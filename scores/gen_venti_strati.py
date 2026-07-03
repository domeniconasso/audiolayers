"""Genera scores/venti-strati.yaml: 20 layer, tempo che ondeggia."""
import math
import yaml

TOTAL = 45.0
random_like = lambda i, k: (math.sin(i * 12.9898 + k * 78.233) * 0.5 + 0.5)


def wave(lo, hi, period, phase, dur, step=1.5):
    """Envelope a onda: oscilla tra lo e hi con periodo e fase dati."""
    pts = []
    t = 0.0
    while t <= dur + 1e-9:
        v = lo + (hi - lo) * (math.sin(2 * math.pi * (t / period) + phase) * 0.5 + 0.5)
        pts.append([round(t, 3), round(v, 4)])
        t += step
    return pts


layers = []
for i in range(20):
    r = lambda k: random_like(i, k)
    onset = round(i * 1.3 * r(1), 2)
    dur = round(min(TOTAL - onset, 12 + 30 * r(2)), 2)
    direction = 1 if i % 2 else -1
    layer = {
        "layer_id": f"strato{i:02d}",
        "onset": onset,
        "duration": dur,
        "pool": "audio/pool/",
        "fill_factor": wave(0.4 + r(3), 1.8 + r(4), 6 + 8 * r(5), r(6) * 6.28, dur),
        "distribution": wave(0.0, 0.9, 10 + 10 * r(7), r(8) * 6.28, dur),
        "pointer": {
            "start": [[0, round(r(9), 3)], [dur, round(r(10), 3)]],
            "start_range": round(0.1 + 0.4 * r(11), 3),
            "overflow": "loop",
        },
        "selection": {"strategy": ["sequential", "rotation", "random"][i % 3]},
        "volume": [[0, -60], [1.5, round(-14 - 8 * r(12), 1)],
                   [dur - 1.5, round(-14 - 8 * r(13), 1)], [dur, -60]],
        "volume_range": round(2 + 4 * r(14), 1),
        "pan": [[0, round(r(15) * 360, 1)],
                [dur, round(r(15) * 360 + direction * (1 + 3 * r(16)) * 360, 1)]],
        "pan_range": round(10 + 30 * r(17), 1),
    }
    if i % 4 == 0:
        # Layer ritmici: accelerando/ritardando ripetuti via onda di BPM.
        layer["fragment"] = {
            "rhythm": {
                "bpm": wave(50 + 40 * r(18), 160 + 80 * r(19), 8 + 6 * r(20),
                            r(21) * 6.28, dur),
                "pattern": [[0.0625, 0.125, 0.0625], [0.125, 0.25],
                            [0.03125, 0.03125, 0.0625, 0.125]][i % 3],
            },
            "attack": 0.004, "release": 0.006,
        }
    else:
        # Layer granulari: la durata dei grani ondeggia -> il tempo
        # rallenta e riparte, con fase diversa per strato.
        layer["fragment"] = {
            "duration": wave(0.008 + 0.01 * r(22), 0.12 + 0.2 * r(23),
                             5 + 9 * r(24), r(25) * 6.28, dur),
            "duration_range": round(0.004 + 0.02 * r(26), 4),
        }
    layers.append(layer)

score = {
    "sample_rate": 48000,
    "seed": 424204,
    "master_volume": 2.0,
    "layers": layers,
}
with open("scores/venti-strati.yaml", "w", encoding="utf-8") as fh:
    fh.write("# 20 strati, tempo a onde: ogni layer accelera e rallenta con\n"
             "# fase propria; pan che ruotano, pointer in transito, selezioni\n"
             "# miste. Generato da gen_venti_strati.py (deterministico).\n")
    yaml.dump(score, fh, sort_keys=False, allow_unicode=True, width=100)
print("layers:", len(layers))
