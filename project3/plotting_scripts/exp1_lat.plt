set xlabel "CBR(Mbps)"
set ylabel "latency(s)"
set title "Latency"
set xrange [0:13]
set xtics 1,1,13
set key outside
set terminal png
set output "exp1_lat.png"
plot "exp1_lat.txt"u 1:2 w lp lw 2 pt 5 title "NewReno","exp1_lat.txt"u 1:3 w lp lw 2 pt 7 title "Reno","exp1_lat.txt"u 1:4 w lp lw 2 pt 9 title "Tahoe","exp1_lat.txt"u 1:5 w lp lw 2 pt 11 title "Vegas"
