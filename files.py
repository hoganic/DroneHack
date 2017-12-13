#!/usr/bin/env python
"""
@authors: Samuel Arwood, Ian Hogan
"""
from numpy import NaN, Inf, complex64, arange, isscalar, asarray, array, \
                  fromfile, fft
from scipy import signal
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
import sys
import os

# 1 for Debug
DEBUG = 0

# Sample rate of the recorded signal
samp_rate = 20000000

# Set t based on the amount of data you want to process per frame. It may take
# some testing to find the rate you need. 
# 20MHz sample rate / 1000 (t) = 50 micro seconds per frame
t = 1000

# Mapping of t samples to the 20MHz sample rate of the HackRF
# Bandwidth of each data frequency is approx 1.8 MHz
bw = 1800000
mapper = (bw*t)/20000000;

# Converted MATLAB function taken from Github
def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    maxtab = []
    mintab = []
       
    if x is None:
        x = arange(len(v))
    
    v = asarray(v)
    
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    
    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    
    lookformax = True
    
    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                if mxpos > t/2:
                    mxpos -= t
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)

# Loop through each file and process the signal       
def processInput(center_freq):            
    
    # Print file output header
    print('*'*80)
    print(' '*30 + 'Output for file ' + center_freq)
    print('*'*80 + '\n\n\n\n')
    
    # Read in current file and set the number of iterations that will 
    # be done over it. iters is controlled by t in the initial section of code
    test = fromfile('./' + center_freq, dtype=complex64)
    iters = int(len(test)/t)
    
    # DEBUG
    # Initialize printing variable
    final = []
    
    # Try and make the output directory again. Maybe we deleted it. 
    #if not os.path.exists('./images/' + center_freq):
    #    os.makedirs('./images/' + center_freq)
    
    # Process each 'frame' of the signal. The frame size is controlled by 
    # iters and t. 
    for frame in range(1, iters):
        
        # Grab each sample, do the fft and get the freq result for graphing
        small_test = test[(frame-1)*t:frame*t]
        test_fft = fft.fft(small_test)
        freq = fft.fftfreq(small_test.shape[-1])
        
        # DEBUG
        # Plot the fft
        if DEBUG:
            plt.plot(freq, abs(test_fft.real)/t)
        
        # Use converted MATLAB function to detect peak within the fft signal
        maxtab, mintab = peakdet(abs(test_fft)/t, .1)
        
        # Initialize variable used for testing
        found = []
        
        # If there are peaks in this frame proceed here. 
        # DEBUG
        # If there are no peaks we append a 0 to the foung array. This gives 
        # us a little more information around when the signal is at it's 
        # maximum while testing. 
        # Non-DEBUG
        # We don't append the 0's to the final array of there were no peaks
        # detected. We only want information directly around the any foung
        # peaks in a given frame.
        if len(maxtab) > 0:
            
            # We are using relative maximum to determine if the points in 
            # maxtab are clustered together
            argmax = signal.argrelmax(maxtab[:,1])
            # Scale the frequency dimension
            maxtab[:,0] = maxtab[:,0]/t
            
            # DEBUG
            # Add the plot of the detected peaks to the current figure, as 
            # well as, the plot of the relative maximums found.
            if DEBUG:
                plt.scatter(array(maxtab)[:,0], \
                            array(maxtab)[:,1], color='red')
                plt.scatter(array(maxtab)[argmax[0],0], \
                            array(maxtab)[argmax[0],1], color='purple')
            else:
                # Non-DEBUG
                # Here we plot the fft, maxtab, and the argmax values if 
                # argmax contains any values. We save these images to a 
                # folder with the same name as the input file in the 
                # images folder.
                if len(argmax[0]) > 0:
                    plt.plot(freq, abs(test_fft.real)/t)
                    plt.scatter(array(maxtab)[:,0], \
                                array(maxtab)[:,1], color='red')
                    plt.scatter(array(maxtab)[argmax[0],0], \
                                array(maxtab)[argmax[0],1], color='purple')
                    plt.savefig('./images/' + center_freq + \
                                    '/' + center_freq + '_' + \
                                    str(frame) + '.png', bbox_inches='tight', \
                                    dpi=90)
                    # Clear the figure for the next plot
                    plt.clf()
                
            # Loop through each of the argmax values. 
            # DEBUG
            # If argmax is 0 we add a zero to the found array.
            for i in range(0, len(argmax[0])):
                
                # Is there only 1 relative maximum?
                if len(argmax[0]) == 1:
                    
                    # DEBUG
                    # Print the frequency of the relative maximum found
                    if DEBUG:
                        print(maxtab[argmax[0][0],0] * samp_rate + \
                              (int(center_freq) * 1000000))
                    # Add the relative maximum to the found and final arrays
                    found.append(maxtab[argmax[0][0],0])
                    final.append([maxtab[argmax[0][0],0], frame])
                # More than one relative maximum
                elif len(argmax[0]) > 1:
                    
                    # Is this the first relative maximum found?
                    if len(found) == 0:
                        # DEBUG
                        # Print the relative maximum value
                        if DEBUG:
                            print(maxtab[argmax[0][i],0] * samp_rate + \
                                  (int(center_freq) * 1000000))
                        # Add the relative maximum to the found and final
                        # arrays
                        found.append(maxtab[argmax[0][i],0])
                        final.append([maxtab[argmax[0][i],0], frame])
                    else:
                        # Initialize a couple variables for determining 
                        # whether or not the new relative max is within the 
                        # same peak of other relative maximums
                        num = len(found)
                        count = 0
                        # Look through each item in the current found array 
                        # and see if the current maximum is too close to 
                        # any of the currently found maxima
                        for item in found:
                            # Is the distance between the two points greater
                            # than the bandwidth? We'll do more processing later
                            if (abs(maxtab[argmax[0][i],0] - item)) > mapper:
                                # Then add to the count
                                count += 1
                                # Is the current maximum greater than everyone
                                # else already found?
                                if count == num:
                                    # DEBUG
                                    # Print the frequency of the maximum
                                    if DEBUG:
                                        print(maxtab[argmax[0][i],0] * samp_rate + \
                                              (int(center_freq) * \
                                               1000000))
                                    # Add the relative maximum to the found
                                    # and final arrays
                                    found.append(maxtab[argmax[0][i],0])
                                    final.append([maxtab[argmax[0][i],0], frame])
            # Add the 0 to found here
            if len(argmax[0]) == 0:
                found.append(0)
        # Add the 0 to found here
        else:
            found.append(0)
                    
        # DEBUG
        # Show the plot of the current frame
        if DEBUG:
            plt.show();
        
    # Loop through each of the entries in final and print them.
    # The output prints the frame number and then the array of found 
    # relative maxima
    for item, frame in final:
        print(str(frame) + "  " + \
              str(item * samp_rate + (int(center_freq) * 1000000)))
    
    # Add some space between files
    print('\n\n\n')
    
    plt.close()
    
# All center frequencies we recorded at. Also the names of the files they
# were recorded into.
file_names = ['2460']#, '2415', '2420', '2425',    \
              #'2430', '2435', '2440', '2445',    \
              #'2450', '2455', '2460', '2465',    \
              #'2470', '2475', '2480', '2485']
               
# Call our function for every signal file
Parallel(n_jobs=1)(delayed(processInput)(i) for i in file_names)
#[processInput(i) for i in file_names]
