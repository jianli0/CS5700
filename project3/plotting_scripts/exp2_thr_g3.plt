set xlabel "CBR(Mbps)"
set ylabel "Throughput"
set title "Throughput"
set xrange [0:13]
set xtics 1,1,13
set key outside
set terminal png
set output "exp2_thr_g3.png"
plot "exp2_thr_g3.txt"u 1:2 w lp lw 2 pt 5 title "Reno","exp2_thr_g3.txt"u 1:3 w lp lw 2 pt 7 title "Reno"
