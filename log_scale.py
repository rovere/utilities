#!/bin/env python


val = 0.0
step = 0.0002
steps_in_one_order_of_magnitude = 5
order_of_magnitude = 6
counter = 0
bins = 1
row = str(val) + ', '
for i in range(0, order_of_magnitude):
 for j in range(counter, steps_in_one_order_of_magnitude):
  val = val + step
#  print val, step, j, i
  bins += 1
  row += str(val) + ', '
  if j == steps_in_one_order_of_magnitude - 1:
    val = val + val
#    print val, step, j, i
    bins += 1
    row += str(val) + ', '
 print row
 row = ''
 step = step*10
 counter = 1
print "Total bins: %d" % bins

