#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@authors: Samuel Arwood, Ian Hogan
"""
import glob
import re
import sys
import numpy as np
from collections import defaultdict, Counter

# Function for printing to the console while the output we want is being
# redirected to a file
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Create a compare "function"
compare = lambda x, y: Counter(x) == Counter(y)

# Debug switch
DEBUG = 0

# Initialize data dict
data = defaultdict(list)

# Grab paths for all the files
script_paths = glob.glob('signals/*_processed')

# Get number of files
numFiles = len(script_paths)

# Grab all the frequency data from the files
for i in range(numFiles):
    lines = [re.findall('\d+', line) for line in open(script_paths[i])]
    data[int(re.findall('\d+', script_paths[i])[0])] = [[int(a), int(b)] for a,b in lines]

# Function for finding patterns in an input file
def find_patterns(file1):

    # Initialize outputs
    output = []
    avg_dist = []

    # Loop through all of the window sizes you want to search within the file.
    # Max windows size is set to 3 (4-1) since we already found out the max pattern
    # size. Originally we set this to a quater of the file entries
    for window_size in range(2, 4):

        # DEBUG
        # Print to stderr the current window size
        if DEBUG:
            eprint(str(window_size))

        # Set the found dictionary
        found_strings = {}

        # Loop through all input file entry by entry, stopping before the window 
        # leaves the file
        for pif in range(len(data[file1])-window_size): 
            # Add each string created by the loop to the dictionary
            found_strings[pif] = tuple(data[file1][pif:pif+window_size])

        # Maybe holds the set, or unique entries in found_strings 
        maybe = set([tuple([y[1] for y in x]) for x in found_strings.values()])
        # Distance holds the frames of the values in found_strings
        distance = [tuple([y[0] for y in x]) for x in found_strings.values()]

        # Now we calulate the distance between every tuple in found_strings
        # If the size is 2 we can just subtract them
        # If the size is 3 we get the distance between (1,2) and (2,3)
        # We need this so that we can try and use the number of frames 
        # as a parameter when sequencing the found values together
        if window_size==2:
            distance = [(x-y) for x,y in distance]
        else:
            distance = [(x-y, y-z) for x,y,z in distance]

        # File specific actions. For 2465 (2475, 2475, 2475) shows up enough
        # in the found list that we need to manual remove it so it doesn't 
        # mess with the results
        if file1 == 2465 and window_size == 3:
            try:
                maybe.remove((2475, 2475, 2475))
            except KeyError:
                pass
            for i in list(found_strings.keys()):
                if ([(x[1]) for x in found_strings[i]] == [2475, 2475, 2475]):
                    del found_strings[i]

        # As long as maybe isn't a copy of found_strings we proceed
        if len(maybe) != len(found_strings.values()):
            # Convert maybe to a list
            save_list = list(maybe)
            # Count the number of times each tuple appears in maybe
            max_maybe = [[tuple([y[1] for y in x]) for x in \
                          found_strings.values()].count(x) for x in save_list]

            # DEBUG
            # Print the patterns found for each window size
            if DEBUG:
                print("Pattern found for ws: " + str(window_size) + ' Max: ' +\
                      str(max(max_maybe)) + ' List: ' +\
                                str(save_list[max_maybe.index(max(max_maybe))]))

            # Add the tuple found the most to output
            output.append([max(max_maybe), \
                      save_list[max_maybe.index(max(max_maybe))]])

            # File specific processing for calculating the average distance between
            # the most found tuple. Not the most elagant but it was late and we 
            # couldn't get the tuples, dictionaries and list to all interact the 
            # way we wanted them to. 
            # 
            # If the value in found_strings matches the check, return their indices
            # from found_string. Append the tuple and its average distance to output
            if file1 == 2460 and window_size == 2:
                indices = [i for i, x in enumerate([tuple([y[1] for y in x]) \
                        for x in found_strings.values()]) if x == (2451, 2463)]
                avg_dist.append([(2451, 2463), abs(sum([distance[x] for x in \
                        indices]))/len(indices)])
            elif file1 == 2465 and window_size == 3:
                indices = [i for i, x in enumerate([tuple([y[1] for y in x]) \
                        for x in found_strings.values()]) if x == (2463, 2471, 2475)]
                avg_dist.append([(2463, 2471, 2475), [abs(sum(y)/len(indices)) \
                        for y in zip(*[distance[x] for x in indices])]])
            elif file1 == 2470 and window_size == 3:
                indices = [i for i, x in enumerate([tuple([y[1] for y in x]) \
                        for x in found_strings.values()]) if x == (2471, 2475, 2463)]
                avg_dist.append([(2471, 2475, 2463), [abs(sum(y)/len(indices)) \
                        for y in zip(*[distance[x] for x in indices])]])
            elif file1 == 2475 and window_size == 2:
                indices = [i for i, x in enumerate([tuple([y[1] for y in x]) \
                        for x in found_strings.values()]) if x == (2471, 2475)]
                avg_dist.append([(2471, 2475), abs(sum([distance[x] for x in \
                        indices]))/len(indices)])
                
    return output, avg_dist

# Call the find patterns function for all 4 files
best_2475, avg_2475 = find_patterns(2475)
# After manual inspection we chose array location 0 as the correct response
best_2475 = best_2475[0]

best_2470, avg_2470 = find_patterns(2470)
# Array location 1 holds the most likely pattern
best_2470 = best_2470[1]

best_2465, avg_2465 = find_patterns(2465)
# Array location 1 holds the most likely pattern
best_2465 = best_2465[1]
    
best_2460, avg_2460 = find_patterns(2460)
# Array location 0 holds the most likely pattern
best_2460 = best_2460[0]

# Print the results
print('2460 ' + str(best_2460) + ' ' + str(avg_2460))
print('2465 ' + str(best_2465) + ' ' + str(avg_2465))
print('2470 ' + str(best_2470) + ' ' + str(avg_2470))
print('2475 ' + str(best_2475) + ' ' + str(avg_2475))
