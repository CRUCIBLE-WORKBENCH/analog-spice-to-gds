"""Connect the native PDK device cells on their generated metal-1 terminals.

Magic coordinates are 0.01 um in this PDK. Layout uses the generated terminal
positions (D=-40, S=40, N gate=128, P gate=332), not device bounding-box edges.
"""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
lines = ["magic", "tech sky130A", "magscale 1 1", "timestamp 0"]
for name, inst, y, bbox in (("nmos", "MN", 0, [-107,-189,107,189]),
                             ("pmos", "MP", 1200, [-125,-411,125,411])):
    lines += [f"use {name} {inst}", "timestamp 0", f"transform 1 0 0 0 1 {y}",
              "box " + " ".join(map(str, bbox))]
lines += ["<< metal1 >>"]
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2
    lines.append(f"rect {min(x1,x2)-12} {min(y1,y2)-12} {max(x1,x2)+12} {max(y1,y2)+12}")
# Input gate connection, outside the right edges of the devices.
for y in (128,1532): wire(0,y,300,y)
wire(300,128,300,1532)
# Joined drains on the left.
for y in (0,1200): wire(-300,y,-40,y)
wire(-300,0,-300,1200)
# Source and substrate/well connections on the right.
wire(40,0,200,0); wire(200,0,200,-250); wire(0,-180,200,-180)
wire(40,1200,200,1200); wire(200,1200,200,816); wire(0,816,200,816)
lines += ["<< labels >>"]
for i,(name,x,y) in enumerate((("vin",300,600),("vout",-300,600),
                                ("vdd",200,1000),("vss",200,-250)),1):
    lines += [f"rlabel metal1 {x} {y} {x} {y} 0 {name}", f"port {i} nsew"]
lines += ["<< end >>"]
(root / "build/amplifier.mag").write_text("\n".join(lines)+"\n")
