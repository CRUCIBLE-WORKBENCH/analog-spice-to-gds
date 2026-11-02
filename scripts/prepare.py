"""Prepare a testbench using the installed PDK without modifying its files."""
from pathlib import Path
import os
import sys
import json

root = Path(__file__).resolve().parents[1]
pdk = Path(os.environ["PDKPATH"])
# Load the exact two TT device model families, avoiding unrelated RF/HV models.
models = pdk / "libs.ref/sky130_fd_pr/spice"
inc = [pdk / "libs.tech/ngspice/parameters/lod.spice"]
for device in ("nfet", "pfet"):
    inc += [models / f"sky130_fd_pr__{device}_01v8__tt.pm3.spice",
            models / f"sky130_fd_pr__{device}_01v8__mismatch.corner.spice"]
header = ".option scale=1u\n.param mc_mm_switch=0 mc_pr_switch=0\n" + "\n".join(f'.include "{p}"' for p in inc)
bench = f"""SKY130 externally biased inverter amplifier
{header}
.include ../spice/amplifier.spice
.temp 27
VDD vdd 0 1.8
VIN vin 0 DC 0.9 AC 1
XAMP vin vout vdd 0 amplifier
CLOAD vout 0 100f
.control
set noaskquit
set wr_singlescale
set wr_vecnames
dc VIN 0.3 1.4 0.0005
wrdata ../results/dc.dat v(vin) v(vout) i(VDD)
quit
.endc
.end
"""
(root / "build/schematic.cir").write_text(bench)
(root / "build/.spiceinit").write_text("set ngbehavior=hsa\n")
if "--characterise" in sys.argv:
    rows = [list(map(float,line.split())) for line in (root / "results/dc.dat").read_text().splitlines()[1:]]
    crossing = next((a,b) for a,b in zip(rows,rows[1:]) if a[2] >= .9 >= b[2])
    a,b = crossing
    bias = a[1] + (.9-a[2])*(b[1]-a[1])/(b[2]-a[2])
    (root / "results/bias.json").write_text(json.dumps({"bias_V":bias,"selection":"linear interpolation of DC Vout=0.9 V crossing"},indent=2))
    for mode,source,cell in (("schematic","../spice/amplifier.spice","amplifier"),
                             ("extracted","amplifier.pex.spice","amplifier_flat")):
        text = f"""SKY130 {mode} amplifier characterisation
{header}
.include {source}
.temp 27
VDD vdd 0 1.8
VIN vin 0 DC {bias:.14g} AC 1 SIN({bias:.14g} 1m 1k)
XAMP vin vout vdd 0 {cell}
CLOAD vout 0 100f
.control
set noaskquit
set wr_singlescale
set wr_vecnames
op
wrdata ../results/{mode}_op.dat v(vin) v(vout) i(VDD)
ac dec 20 10 1G
let gain_mag=mag(v(vout))
let gain_phase=180/PI*cph(v(vout))
wrdata ../results/{mode}_ac.dat gain_mag gain_phase
tran 1u 5m 0 1u
wrdata ../results/{mode}_tran.dat v(vin) v(vout) i(VDD)
quit
.endc
.end
"""
        (root / f"build/{mode}_characterise.cir").write_text(text)
