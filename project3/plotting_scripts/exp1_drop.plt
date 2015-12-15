set xlabel "CBR(Mbps)"
set ylabel "Droprate"
set title "Droprate"
set xrange [0:13]
set xtics 1,1,13
set key outside
set terminal png
set output "exp1_drop.png"
plot "exp1_drop.txt"u 1:2 w lp lw 2 pt 5 title "NewReno","exp1_drop.txt"u 1:3 w lp lw 2 pt 7 title "Reno","exp1_drop.txt"u 1:4 w lp lw 2 pt 9 title "Tahoe","exp1_drop.txt"u 1:5 w lp lw 2 pt 11 title "Vegas"
