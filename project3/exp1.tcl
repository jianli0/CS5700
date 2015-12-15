#Create a simulator object
set ns [new Simulator]

#Read rate of cbr and variant of tcp from the command line
#Check availbility of inputs
if {$argc != 2} {
        puts "The script requires two numbers to be inputed"
        puts "The first parameter represents the rate of the cbr"
        puts "The second parameter represents the variants of tcp"
        exit 1
}

#Open the trace file
set trace_name exp1_trace/
if {[lindex $argv 1] == "TCP"} {
        append trace_name Tahoe_cbr_
} else {
        append trace_name [lindex [split [lindex $argv 1] /] 1]_cbr_
}
append trace_name [lindex $argv 0].tr
set nf [open $trace_name w]
$ns trace-all $nf

#Define a 'finish' procedure
proc finish {} {
        global ns nf
        $ns flush-trace
        #Close the trace file
        close $nf
        exit 0
}

#Create six nodes
set n0 [$ns node]
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]

#Create links between the nodes using DropTail
$ns duplex-link $n0 $n1 10Mb 10ms DropTail
$ns duplex-link $n1 $n4 10Mb 10ms DropTail
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n2 $n5 10Mb 10ms DropTail

#Create a UDP agent and attach it to node n2
set udp [new Agent/UDP]
$ns attach-agent $n1 $udp
#Create a Null agent (a traffic sink) and attach it to node n3
set null [new Agent/Null]
$ns attach-agent $n2 $null
# Create a CBR traffic source and attach it to udp0
set val [lindex $argv 0]Mb
set cbr [new Application/Traffic/CBR]
$cbr set rate_ $val
$cbr attach-agent $udp

set tcp [new Agent/[lindex $argv 1]]
$ns attach-agent $n0 $tcp

set sink [new Agent/TCPSink]
$ns attach-agent $n3 $sink

$ns connect $udp $null
$udp set fid_ 1
$ns connect $tcp $sink
$tcp set fid_ 2

set ftp [new Application/FTP]
$ftp attach-agent $tcp

#Schedule events for the CBR agents
$ns at 0.0 "$cbr start"
$ns at 0.0 "$ftp start"
$ns at 10.0 "$ftp stop"
$ns at 10.0 "$cbr stop"
#Call the finish procedure after 5 seconds of simulation time
$ns at 10.5 "finish"

#Run the simulation
$ns run

