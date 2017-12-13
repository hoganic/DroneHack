#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@authors: Samuel Arwood, Ian Hogan
"""
import re
import numpy as np

# Change this to the currently running file
file_num = '2475'

# Read in the file output from files.py
with open(file_num +'.txt', 'r') as f:
    content = f.readlines()

# Initialize data arrays
data = []
output = []    

# Use regex to pull out the info you need from the file output
# and add it to the data array
for line in content:
    re1 = '(\\d+)'
    re2 = '(\\s+)'
    re3 = '([+-]?\\d*\\.\\d+)(?![-+0-9\\.])'
    
    rg = re.compile(re1+re2+re3, re.IGNORECASE|re.DOTALL)
    m = rg.search(line)
    if m:
        data.append([int(m.group(1)), float(m.group(3))])

# Process the data only filtering on relative frequency changes and changes
# over time. 
# 700 - number of frames between peaks before we will readd it to the list
# 900000 - half the bandwidth - ignore close peaks over time (700 frames)
def process():
    for x in range(0, len(data)):
    
        if not output:
            output.append(data[x])
        elif ((data[x][0] - output[-1][0]) < 700):
            if (abs(data[x][1] - output[-1][1])) > 900000:
                output.append(data[x])
        else:
            output.append(data[x])

# Call the process function, weren't sure if we would need to call it again
# or if we could process multiple files at a time
process()

# Manual tweaks for our data

# 2.475GHz shows up as 2.455GHz because of an issue with GNU Radio 
def wrap_around(freq):
    output[freq][1] = 2475000000

# 2.467GHz was deemed to be noise or a harmonic
def kill_2467(freq):
    output[freq][1] = 0
    
# 2.478GHz was deemed to be noise or a harmonic
def kill_2478(freq):
    output[freq][1] = 0
    
# 2.462GHz was a rounding error for 2.463GHz
def correct_2462(freq):
    output[freq][1] = 2463000000
    
# 2.474GHz and 2.476GHz were rounding errors for 2.475GHz
def correct_2476_2474(freq):
    output[freq][1] = 2475000000
    
# Makeshift Python switch statement
options = {'2455' : wrap_around,
           '2467' : kill_2467,
           '2478' : kill_2478,
           '2462' : correct_2462,
           '2476' : correct_2476_2474,
           '2474' : correct_2476_2474,
           }

# Process the output array for any of the errors listed in the switch
# function list above
for freq in range(len(output)):
    try:
        options[str(round(output[freq][1]/1000000))](freq)
    except KeyError:
        pass

# Delete the killed entries
for x in output[:]:
    if x[1] == 0:
        output.remove(x)

# Reprocess the data now that we made changes to it
data = output
process()

# Write the output to a file for later processing
with open(file_num + '_processed', 'w') as f:
    for a in output:
        f.writelines(str(a[0]) + '  ' + str(round(a[1]/1000000)) + '\n')
