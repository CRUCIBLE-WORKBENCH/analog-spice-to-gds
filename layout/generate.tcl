# First inspect the native PDK-generated device geometry before routing.
set root [file normalize [file join [file dirname [info script]] ..]]
cd [file join $root build]
file delete nmos.mag pmos.mag
load nmos
snap internal
box values 5um 5um 5um 5um
set n [sky130::sky130_fd_pr__nfet_01v8_defaults]
dict set n w 2
dict set n l 0.5
dict set n guard 1
dict set n full_metal 1
dict set n viagb 100
puts "NMOS_PARAMS $n"
puts "NMOS_BOX [sky130::sky130_fd_pr__nfet_01v8_draw $n]"
save nmos.mag
load pmos
set p [sky130::sky130_fd_pr__pfet_01v8_defaults]
dict set p w 6
dict set p l 0.5
dict set p guard 1
dict set p full_metal 1
dict set p viagb 100
puts "PMOS_PARAMS $p"
puts "PMOS_BOX [sky130::sky130_fd_pr__pfet_01v8_draw $p]"
save pmos.mag
extract all
ext2spice lvs
ext2spice -o devices.spice
quit -noprompt
