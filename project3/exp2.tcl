#Create a simulator object
set ns [new Simulator]

#Read rate of cbr and variant of tcp from the command line
#Check availbility of inputs
if {$argc != 3} {
        puts "The script requires 3 numbers to be inputed"
        puts "The first parameter represents the rate of the cbr"
        puts "The second parameter represents the first variant of tcp"
        puts "The third parameter represents the second variant of tcp"
        exit 1
}

#Open the trace file
set trace_name exp2_trace/
append trace_name [lindex [split [lindex $argv 1] /] 1]_
append trace_name [lindex [split [lindex $argv 2] /] 1]_cbr_
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
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

#Create links between the nodes using DropTail
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n5 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n3 $n4 10Mb 10ms DropTail
$ns duplex-link $n3 $n6 10Mb 10ms DropTail

#Set CBR agent.
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
set cbr [new Application/Traffic/CBR]
$cbr set rate_ [lindex $argv 0]Mb
$cbr attach-agent $udp

#Create a Null agent (a traffic sink) and attach it to node n3
set null [new Agent/Null]
$ns attach-agent $n3 $null

#Create 2 TCP agents and attach them s to node n1 and n5 respectively
set type1 Agent/
set type2 Agent/
append type1 [lindex $argv 1]
append type2 [lindex $argv 2]
set tcp0 [new $type1]
set tcp1 [new $type2]
$ns attach-agent $n1 $tcp0
$ns attach-agent $n5 $tcp1

# Create 2 FTP and attach them to tcp0 and tcp1
set ftp0 [new Application/FTP]
set ftp1 [new Application/FTP]
$ftp0 attach-agent $tcp0
$ftp1 attach-agent $tcp1

#Create a SINK agent (a TCP sink) and attach it to the node n4 and n6
set sink0 [new Agent/TCPSink]
$ns attach-agent $n4 $sink0
set sink1 [new Agent/TCPSink]
$ns attach-agent $n6 $sink1

#Connect the traffic sources with the traffic sink
$ns connect $udp $null
$udp set fid_ 3
$ns connect $tcp0 $sink0
$tcp0 set fid_ 1
$ns connect $tcp1 $sink1
$tcp1 set fid_ 2

#Schedule events for the CBR agents
$ns at 0.0 "$cbr start"
$ns at 0.0 "$ftp0 start"
$ns at 0.0 "$ftp1 start"
$ns at 10.0 "$ftp0 stop"
$ns at 10.0 "$ftp1 stop"
$ns at 10.0 "$cbr stop"
#Call the finish procedure after 5 seconds of simulation time
$ns at 15.0 "finish"

#Run the simulation
$ns run