#!/usr/bin/env bash
set -euo pipefail
export LD_LIBRARY_PATH="${MAGIC_RUNTIME_DIR:-$MAGIC_LOCAL/../../runtime/usr/lib/x86_64-linux-gnu}:$MAGIC_LOCAL/lib:$MAGIC_LOCAL/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export TCL_LIBRARY="$MAGIC_LOCAL/lib/tcl8.6"
export TK_LIBRARY="$MAGIC_LOCAL/lib/tk8.6"
export CAD_ROOT="$MAGIC_LOCAL/lib"
ulimit -Sn 1024
exec "$MAGIC_LOCAL/bin/magic" -dnull -noconsole -rcfile layout/project.magicrc "$1"
