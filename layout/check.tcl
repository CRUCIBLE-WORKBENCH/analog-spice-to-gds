set root [file normalize [file join [file dirname [info script]] ..]]
cd [file join $root build]
load amplifier
select top cell
expand
drc check
drc catchup
puts "AMPLIFIER_DRC_COUNT [drc list count total]"
puts "AMPLIFIER_DRC_DETAILS [drc listall why]"
gds write amplifier.gds
flatten amplifier_flat
load amplifier_flat
select top cell
extract all
ext2spice lvs
ext2spice -o amplifier.lvs.spice
ext2spice cthresh 0
ext2spice -o amplifier.pex.spice
puts "AMPLIFIER_EXTRACTION_FINISHED"
quit -noprompt
