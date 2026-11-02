#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/runtime results
source scripts/paths.sh
export LD_LIBRARY_PATH="$PWD/build/runtime${NGSPICE_RUNTIME_DIR:+:$NGSPICE_RUNTIME_DIR}:${LD_LIBRARY_PATH:-}"
case "${1:-sim}" in
  sim) cd build; igny run --env analog-spice-gds ngspice -b -o ../results/schematic.log schematic.cir ;;
  prepare) python3 scripts/prepare.py ;;
  layout)
    igny run script --env analog-spice-gds scripts/magic_local.sh -- layout/generate.tcl
    python3 scripts/route.py
    igny run script --env analog-spice-gds scripts/magic_local.sh -- layout/check.tcl
    ;;
  lvs)
    igny run --env analog-spice-gds netgen -batch lvs \
      'build/amplifier.lvs.spice amplifier_flat' 'spice/amplifier.spice amplifier' \
      "$PDKPATH/libs.tech/netgen/sky130A_setup.tcl" results/lvs.log
    python3 -c 'from pathlib import Path; p=Path("spice/amplifier.spice"); Path("build/disconnected.spice").write_text(p.read_text().replace("XP vout vin", "XP vout disconnected_gate"))'
    igny run --env analog-spice-gds netgen -batch lvs \
      'build/amplifier.lvs.spice amplifier_flat' 'build/disconnected.spice amplifier' \
      "$PDKPATH/libs.tech/netgen/sky130A_setup.tcl" results/lvs_negative.log
    ;;
  characterise)
    python3 scripts/prepare.py --characterise
    cd build
    for mode in schematic extracted; do
      timeout 120 igny run --env analog-spice-gds ngspice -b -o "../results/${mode}_characterise.log" "${mode}_characterise.cir"
    done
    ;;
  *) echo "Expected sim or layout" >&2; exit 2 ;;
esac
