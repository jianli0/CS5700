from collections import OrderedDict
import os
exp1_tcps = ["Newreno", "Reno", "Tahoe", "Vegas"]
exp2_tcps = ["Newreno_Reno", "Reno_Reno", "Newreno_Vegas", "Vegas_Vegas"]
TCP_VARIANTS = ['Reno', 'Sack1']
QUEUING_VARIANTS= ['RED', 'DropTail']


def calculate_benchmarks_exp1(fname):
    total_packets_sent = total_packets_received = 0
    window = {}
    sum_delay = 0
    end_time = 0
    start_time = -1

    for line in open(fname):
        event, time, start, end, ptype, size, _, _, source, dest, seq, _ = line.split()

        if ptype == "tcp" and event == "-" and start == "0":
            total_packets_sent += 1
            window[seq] = float(time)
            if start_time < 0:
                start_time = float(time)

        if ptype == "ack" and event == "r" and end == "0" and seq in window:
            total_packets_received += 1
            end_time = float(time)
            sum_delay += float(time) - window.pop(seq)

    delay = sum_delay / total_packets_received
    droprate = 1- float(total_packets_received)/total_packets_sent
    througput = (total_packets_received * 8 * 1040)/ (end_time - start_time) / 1000000

    return througput, droprate, delay


def calculate_benchmarks_exp2(fname):
    total_packets_sent_1 = total_packets_received_1 = 0
    total_packets_sent_2 = total_packets_received_2 = 0
    window_1 = {}
    window_2 = {}
    sum_delay_1 = sum_delay_2 = 0
    end_time_1 = end_time_2 = 0
    start_time_1 = start_time_2 = -1

    for line in open(fname):
        event, time, start, end, ptype, size, _, fid, source, dest, seq, _ = line.split()

        if ptype == "tcp" and event == "-" and float(start) == float(source):
            if fid == "1":
                total_packets_sent_1 += 1
                window_1[seq] = float(time)
                if start_time_1 < 0:
                    start_time_1 = float(time)
            else:
                total_packets_sent_2 += 1
                window_2[seq] = float(time)
                if start_time_2 < 0:
                    start_time_2 = float(time)              

        if ptype == "ack" and event == "r" and float(end) == float(dest):
            if fid == "1" and seq in window_1:
                total_packets_received_1 += 1
                end_time_1 = float(time)
                sum_delay_1 += float(time) - window_1.pop(seq)
            elif fid == "2"  and seq in window_2:
                total_packets_received_2 += 1
                end_time_2 = float(time)
                sum_delay_2 += float(time) - window_2.pop(seq)

    delay_1 = sum_delay_1 / total_packets_received_1
    droprate_1 = 1- float(total_packets_received_1)/total_packets_sent_1
    througput_1 = (total_packets_received_1 * 1040 * 8)/ (end_time_1 - start_time_1) / 1000000
    
    delay_2 = sum_delay_2 / total_packets_received_2
    droprate_2 = 1- float(total_packets_received_2)/total_packets_sent_2
    througput_2 = (total_packets_received_2 * 1040 * 8)/ (end_time_2 - start_time_2) / 1000000

    return througput_1, droprate_1, delay_1, througput_2, droprate_2, delay_2


def calculate_benchmarks_exp3(fname):
    total_received_size = total_packets_received = 0
    window = {}
    sum_delay = 0
    end_time = 0
    start_time = 0

    for line in open(fname):
        event, time, start, end, ptype, size, _, _, source, dest, seq, _ = line.split()
        time = float(time)
        if ptype == "tcp" and event == "-" and start == "0":
            window[seq] = time

        if ptype == "ack" and event == "r" and end == "0" and seq in window:
            total_packets_received += 1
            sum_delay += max(time - window.pop(seq), 0)

        if time - start_time >= 1:
            delay = sum_delay / total_packets_received
            througput = (total_packets_received * 8 * 1040)/ (time - start_time) / 1000000

            sum_delay = 0
            start_time = time
            window = {}
            total_received_size = total_packets_sent = total_packets_received = 0        
            yield int(time), round(througput, 3), round(delay, 3)


def output_benchmarks_exp1():
    fname_format = "exp1_trace/%s_cbr_%d.tr"
    tp_file = open("exp1_throughput.dat", "w")
    lat_file = open("exp1_delay.dat", "w")
    dr_file = open("exp1_droprate.dat", "w")
    
    tp_content = ""
    lat_content = ""
    dr_content = ""


    for cbr_rate in range(1, 11):
        tp_content += str(cbr_rate)
        lat_content += str(cbr_rate)
        dr_content += str(cbr_rate)
        for prefix in exp1_tcps:
            tp, dr, lat = calculate_benchmarks_exp1(fname_format % (prefix, cbr_rate))
            tp_content += "\t%f" % tp
            lat_content += "\t%f" % lat
            dr_content += "\t%f" % dr

        tp_content += "\n"
        dr_content += "\n"
        lat_content += "\n"

    tp_file.write(tp_content)
    dr_file.write(dr_content)
    lat_file.write(lat_content)
    tp_file.close()
    lat_file.close()
    dr_file.close()


def output_benchmarks_exp2():
    fname_format = "exp2_trace/%s_cbr_%d.tr"

    for prefix in exp2_tcps:
        tp_file = open("exp2_throughput_%s.dat" % prefix, "w")
        lat_file = open("exp2_delay_%s.dat" % prefix, "w")
        dr_file = open("exp2_droprate_%s.dat" % prefix, "w")
        tp_content = ""
        lat_content = ""
        dr_content = ""

        for cbr_rate in range(1, 11):
            tp_content += str(cbr_rate)
            lat_content += str(cbr_rate)
            dr_content += str(cbr_rate)     
            tp_1, dr_1, lat_1, tp_2, dr_2, lat_2 = calculate_benchmarks_exp2(fname_format % (prefix, cbr_rate))
            tp_content += "\t%f\t%f\n" % (tp_1, tp_2)
            lat_content += "\t%f\t%f\n" % (lat_1, lat_2)
            dr_content += "\t%f\t%f\n" % (dr_1, dr_2)

        tp_file.write(tp_content)
        dr_file.write(dr_content)
        lat_file.write(lat_content)
        tp_file.close()
        lat_file.close()
        dr_file.close()


def output_benchmarks_exp3():
    tp_file = open("exp3_throughput.dat", "w")
    lat_file = open("exp3_delay.dat", "w")
    tp_columns = OrderedDict({second: [] for second in range(21)})
    lat_columns = OrderedDict({second: [] for second in range(21)})

    for tcp in TCP_VARIANTS:
        for queue in QUEUING_VARIANTS:
            fname = "exp3_trace/" + tcp + "_" + queue + ".tr"
            for time, tp, lat in calculate_benchmarks_exp3(fname):
                tp_columns[time].append(tp)
                lat_columns[time].append(lat)

    for time, tps in tp_columns.iteritems():
        if tps:
            tp_file.write("%d\t%.3f\t%.3f\t%.3f\t%.3f\n" % (time, tps[0], tps[1], tps[2], tps[3]))
        else: tp_file.write("0\t0.000\t0.000\t0.000\t0.000\n")    
    for time, lats in lat_columns.iteritems():
        if lats:
            lat_file.write("%d\t%.3f\t%.3f\t%.3f\t%.3f\n" % (time, lats[0], lats[1], lats[2], lats[3]))
        else:
            lat_file.write("0\t0.000\t0.000\t0.000\t0.000\n")
    
    tp_file.close()
    lat_file.close()
    
def generate_logs():
    exp1_cmd = "ns exp1.tcl %d %s"
    exp2_cmd = "ns exp2.tcl %d %s %s"
    exp3_cmd = "ns exp3.tcl %s %s"

    for var in exp1_tcps:
        var = "TCP/" + var if var != "Tahoe" else "TCP"
        for cbr in range(1, 11): os.system(exp1_cmd % (cbr, var))
    
    for var in exp2_tcps:
        tcp1, tcp2 = var.split("_")
        for cbr in range(1, 11): os.system(exp2_cmd % (cbr, "TCP/" + tcp1, "TCP/" + tcp2))

    for tcp in TCP_VARIANTS:
        for queue in QUEUING_VARIANTS:
            os.system(exp3_cmd % (queue, tcp))


if __name__ == '__main__':
    generate_logs()
    output_benchmarks_exp1()
    output_benchmarks_exp2()
    output_benchmarks_exp3()
