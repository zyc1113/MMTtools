"""
mmirs_qrp
=========

Python script that quickly reduces longslit and MOS spectra from MMT/MMIRS
"""

import sys, os

from chun_codes import systime

from os.path import exists
from astropy.io import ascii as asc
from astropy.io import fits

from scipy.ndimage.interpolation import shift

import numpy as np

import matplotlib.pyplot as plt
import glob

from astropy.table import Table
from astropy import log

def main(rawdir, prefix, bright=False, dither='ABApBp', silent=False,
         verbose=True):

    '''
    Main function of mmirs_qrp

    Parameters
    ----------

    silent : boolean
      Turns off stdout messages. Default: False

    verbose : boolean
      Turns on additional stdout messages. Default: True

    Returns
    -------

    Notes
    -----
    Created by Chun Ly, 13 October 2017
     - Handle gzip files as inputs
     - Change data cube dimensions
     - Handle FITS overwrite
     - Added dithering keyword
     - Handle ABA'B' dithering to get "sky" frame
     - AB subtraction for background removal
     - Add difference data cube for combine
     - Compute average from background-subtracted, image-shifted images
    Modified by Chun Ly, 14 October 2017
     - Bug in shift call. Need to specify as row,column shift values
    '''
    
    if silent == False: log.info('### Begin main : '+systime())

    if rawdir[-1] != '/': rawdir = rawdir + '/'

    dcorr_files = glob.glob(rawdir+prefix+'*dcorr.fits*')
    n_files     = len(dcorr_files)
    
    hdu0 = fits.getheader(dcorr_files[0])
    naxis1, naxis2 = hdu0['NAXIS1'], hdu0['NAXIS2']
    
    d_cube0     = np.zeros((n_files, naxis1, naxis2))
    peak_val    = np.zeros(n_files)
    shift_cube0 = np.zeros((n_files, naxis1, naxis2))

    dither_cat  = np.zeros(n_files)
    diff_cube0  = np.zeros((n_files, naxis1, naxis2))

    if dither == 'ABApBp':
        i_off = [1, -1] * (n_files/2)
        if n_files % 2 == 1: i_off.append(-1) # Odd number correction
        i_sky = np.arange(n_files)+np.array(i_off)
    print i_sky

    for ii in range(n_files):
        d_cube0[ii], t_hdr = fits.getdata(dcorr_files[ii], header=True)
        dither_cat[ii] = t_hdr['INSTEL']

        t_sky  = fits.getdata(dcorr_files[i_sky[ii]])
        t_diff = d_cube0[ii] - t_sky
        diff_cube0[ii] = t_diff

        # Compute offsets using bright source
        if bright == True:
            med0_row = np.median(t_diff, axis=1)

            resize   = np.repeat(med0_row, naxis1).reshape((naxis2,naxis1))
            im_test  = t_diff - resize

            med0_col     = np.median(im_test, axis=0)
            peak_val[ii] = np.argmax(med0_col)
        else:
            log.info('### Not supported yet')

    shift_val = peak_val[0] - peak_val

    # Fix bug on 13/10/2017
    log.info('### Shift values for spectra : ')
    log.info('### '+" ".join([str(a) for a in shift_val]))

    for ii in range(n_files):
        # Bug fix - Mod on 14/10/2017
        shift_cube0[ii] = shift(diff_cube0[ii], [0,shift_val[ii]])

    stack0 = np.average(shift_cube0, axis=0)

    fits.writeto(rawdir+prefix+'_stack.fits', stack0, overwrite=True)

    if silent == False: log.info('### End main : '+systime())
#enddef

