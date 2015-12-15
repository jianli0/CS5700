###Group Members:
- Kexi Long	001729512
- Jian Li	001731714

###Usage:
First create 3 dirs for storing trace files.
`mkdir exp1_trace`
`mkdir exp2_trace`
`mkdir exp3_trace`

Then run TCL scripts manually to generate trace files.
For example,
`ns exp1.tcl <cbr_rate> <tcp_variant>`
`ns exp2.tcl <cbr_rate> <tcp_variant_1> <tcp_variant_2>`
`ns exp2.tcl <queue_discipline> <tcp_variant>`

At last, run parser to aggregate logs to generate chart data.
`python aggregate_logs`

