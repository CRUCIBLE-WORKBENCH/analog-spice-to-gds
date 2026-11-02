"""Independent numerical and physical artifact checks for the amplifier demo."""
from pathlib import Path
import json
import re
import sys
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"

def table(name):
    a = np.loadtxt(R / name, skiprows=1)
    assert np.isfinite(a).all(), name + ": non-finite data"
    return np.atleast_2d(a)

def measure(ac, tran, op):
    i = np.argmin(abs(ac[:,0] - 1000))
    assert abs(ac[i,0]-1000) < 1, "1 kHz sample missing"
    gain = float(ac[i,1])
    assert gain > 5, "AC gain below target"
    assert abs(op[0,2]-.9) < .02, "wrong operating point"
    assert 0 < -op[0,3] < .001, "invalid supply current"
    a = tran[tran[:,0] >= .003]
    assert len(a) > 1500 and a[-1,0] >= .005, "transient too short"
    basis = np.column_stack((np.ones(len(a)), np.sin(2*np.pi*1000*a[:,0]), np.cos(2*np.pi*1000*a[:,0])))
    vi = np.linalg.lstsq(basis, a[:,1], rcond=None)[0]
    vo = np.linalg.lstsq(basis, a[:,2], rcond=None)[0]
    signed_gain = float(vo[1]/vi[1])
    assert signed_gain < -5, "transient is not an inverting amplifier"
    assert abs(abs(signed_gain)/gain-1) < .10, "transient and AC disagree"
    return dict(gain_1k_V_V=gain, transient_signed_gain=signed_gain,
                output_bias_V=float(op[0,2]), supply_current_A=float(-op[0,3]),
                phase_1k_deg=float(ac[i,2]),
                output_peak_V=float(np.hypot(vo[1],vo[2])))

def simulation():
    results = {}
    for mode in ("schematic", "extracted"):
        ac,tran,op = [table(f"{mode}_{suffix}.dat") for suffix in ("ac","tran","op")]
        results[mode] = measure(ac,tran,op)
        # Same observer must reject loss of amplification and inversion.
        for bad in ("flat", "noninverting"):
            altered = tran.copy()
            altered[:,2] = op[0,2] if bad == "flat" else 2*op[0,2]-tran[:,2]
            try: measure(ac,altered,op)
            except AssertionError: pass
            else: raise AssertionError("numerical negative control accepted: " + bad)
        log = (R / f"{mode}_characterise.log").read_text()
        assert "ngspice-46 done" in log and not re.search(r"(?im)^\s*(error|fatal)\b", log)
    assert abs(results["extracted"]["gain_1k_V_V"]/results["schematic"]["gain_1k_V_V"]-1) < .20
    dc = table("dc.dat")
    assert len(dc) >= 2000 and dc[0,2] > 1.7 and dc[-1,2] < .1
    results["bias_selection"] = json.loads((R / "bias.json").read_text())
    (R / "measurements.json").write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps(results,indent=2))
    print("AMPLIFIER_SIMULATION_VERIFIED_WITH_NEGATIVE_CONTROLS")

def physical():
    import klayout.db as kdb
    log = (R / "layout.log").read_text()
    counts = re.findall(r"AMPLIFIER_DRC_COUNT (\d+)",log)
    assert counts == ["0"], counts
    assert "AMPLIFIER_EXTRACTION_FINISHED" in log
    lvs = (R / "lvs.log").read_text()
    assert "Final result: Circuits match uniquely." in lvs
    assert "Number of devices: 2" in lvs and "Number of nets: 4" in lvs
    layout = kdb.Layout()
    layout.read(str(ROOT / "build/amplifier.gds"))
    tops = layout.top_cells()
    assert len(tops) == 1 and tops[0].name == "amplifier"
    count = sum(tops[0].shapes(i).size() for i in layout.layer_indexes())
    assert count >= 10 and layout.cells() >= 3
    pex = (ROOT / "build/amplifier.pex.spice").read_text()
    caps = re.findall(r"(?m)^C\d+\s",pex)
    assert len(caps) >= 5
    negative = (R / "lvs_negative.log").read_text()
    assert "Circuits match uniquely" not in negative
    assert re.search(r"do not match|Mismatch|mismatch|unmatched|different",negative)
    receipt = dict(top=tops[0].name,cells=layout.cells(),top_shapes=count,
                   bbox_um=[tops[0].bbox().left*layout.dbu,tops[0].bbox().bottom*layout.dbu,
                            tops[0].bbox().right*layout.dbu,tops[0].bbox().top*layout.dbu],
                   extracted_capacitors=len(caps),magic_drc_errors=0,
                   lvs="unique match; disconnected-gate control rejected",
                   gds_sha256=hashlib.sha256((ROOT / "build/amplifier.gds").read_bytes()).hexdigest())
    (R / "physical.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    print("AMPLIFIER_PHYSICAL_ARTIFACTS_VERIFIED")

if __name__ == "__main__":
    {"simulation":simulation,"physical":physical}[sys.argv[1]]()
