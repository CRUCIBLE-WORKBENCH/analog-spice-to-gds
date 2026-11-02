#!/usr/bin/env bash
# Optional machine configuration is deliberately excluded from Git.
if [ -f local.env.sh ]; then source ./local.env.sh; fi
export PDKPATH="${AMPLIFIER_PDK:-${PDKPATH:-}}"
: "${PDKPATH:?Set AMPLIFIER_PDK to a complete SKY130A PDK}"
: "${MAGIC_LOCAL:?Set MAGIC_LOCAL to the Tcl-capable Magic payload root}"
export MAGIC_LOCAL
