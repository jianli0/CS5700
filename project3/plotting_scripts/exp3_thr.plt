set xlabel "CBR(Mbps)"
set ylabel "Throughput"
set title "Throughput"
set xrange [0:20]
set yrange [0:3]
set xtics 1,1,20
set key outside
set terminal png
set output "exp3_thr.png"
plot "exp3_thr.txt"u 1:2 w lp lw 2 pt 5 title "Reno-RED","exp3_thr.txt"u 1:3 w lp lw 2 pt 7 title "Reno-DropTail","exp3_thr.txt"u 1:4 w lp lw 2 pt 9 title "Sack-RED","exp3_thr.txt"u 1:5 w lp lw 2 pt 11 title "Sack-DropTail"
