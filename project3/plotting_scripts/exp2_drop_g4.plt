set xlabel "CBR(Mbps)"
set ylabel "Droprate"
set title "Droprate"
set xrange [0:13]
set xtics 1,1,13
set key outside
set terminal png
set output "exp2_drop_g4.png"
plot "exp2_drop_g4.txt"u 1:2 w lp lw 2 pt 5 title "Vegas","exp2_drop_g4.txt"u 1:3 w lp lw 2 pt 7 title "Vegas"
