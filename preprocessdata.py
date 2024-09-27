#ref: https://github.com/dlakaplan/JWSTTiming
#Create ePSF of NIRCam data, then apply to the reduced JWST data from PID: 1666
#Original Author: Aarran Shaw
#Editor: Phornsawan Roemsri
#Based on:
#https://spacetelescope.github.io/jdat_notebooks/notebooks/psf_photometry/NIRCam_PSF_Photometry_Example.html
#https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-performance/nircam-point-spread-functions

#data located at:

# seg1 (sw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg001_nrcb1/
# seg1 (lw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg001_nrcblong/
# seg2 (sw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg002_nrcb1/
# seg2 (lw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg002_nrcblong/
# seg3 (sw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg003_nrcb1/
# seg3 (lw) /Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/jw01666001001_02102_00001-seg003_nrcblong/

#files:

#jw01666001001_02102_00001-seg001_nrcb1_o001_crfints.fits
#jw01666001001_02102_00001-seg001_nrcblong_o001_crfints.fits
#jw01666001001_02102_00001-seg002_nrcb1_o001_crfints.fits
#jw01666001001_02102_00001-seg002_nrcblong_o001_crfints.fits
#jw01666001001_02102_00001-seg003_nrcb1_o001_crfints.fits
#jw01666001001_02102_00001-seg003_nrcblong_o001_crfints.fits

import numpy as np
import scipy.stats as st
import webbpsf
import matplotlib.pyplot as plt
from astropy import units as u, constants as c
from astropy.io import fits
# from synphot import SourceSpectrum, units, ReddeningLaw, SpectralElement
# from synphot.models import BlackBodyNorm1D
from photutils.background import MMMBackground, MADStdBackgroundRMS, SExtractorBackground
from astropy.modeling.fitting import LevMarLSQFitter
from photutils.psf import IntegratedGaussianPRF, SourceGrouper, FittableImageModel, PSFPhotometry
from photutils.detection import IRAFStarFinder, DAOStarFinder
from astropy.visualization import ZScaleInterval
import inspect
import glob
import copy
from photutils.centroids import centroid_sources
from photutils.centroids import (
    centroid_1dg,
    centroid_2dg,
    centroid_com,
    centroid_quadratic,
)
from photutils.aperture import (
    CircularAperture,
    CircularAnnulus,
    ApertureStats,
    aperture_photometry,
)
import photutils.psf.utils
from astropy.stats import SigmaClip
from astropy.table  import Table
from astropy.time import Time

import os
import time
from pymongo import MongoClient
import pprint
import json
from pathlib import Path

# Define the path of webbpsf-data using pathlib
path = Path('./static/lib/webbpsf-data')
# Set the environment variable, Convert the Path object to a string and set the environment variable
os.environ['WEBBPSF_PATH'] = str(path)

client = MongoClient()
client = MongoClient("localhost", 27017)
client = MongoClient("mongodb://localhost:27017/")
db = client.jwst
collection = db.ZTF_J1539




#define a nansumwrapper so it returns nan if all numbers are nans but does things properly if there only a few nans
def nansumwrapper(a, **kwargs):
    if np.isnan(a).all():
        return np.nan
    else:
        return np.nansum(a, **kwargs)
    

def convert_time_units(mjd_times, unit):
    """
    Convert a list of Modified Julian Date (MJD) times to the specified unit.

    Parameters:
    - mjd_times (list or np.array): List of MJD times.
    - unit (str): Unit to convert to. Supported units are 'second', 'minute', 'hour', 'day'.

    Returns:
    - converted_times (np.array): Array of times converted to the specified unit.
    """
    time_sorted = Time(mjd_times, format="mjd", scale="tdb")

    if unit == 'second':
        converted_times = (time_sorted.mjd - time_sorted.mjd.min()) * 86400.0  # seconds
    elif unit == 'minute':
        converted_times = (time_sorted.mjd - time_sorted.mjd.min()) * 1440.0  # minutes
    elif unit == 'hour':
        converted_times = (time_sorted.mjd - time_sorted.mjd.min()) * 24.0  # hours
    elif unit == 'day':
        converted_times = time_sorted.mjd - time_sorted.mjd.min()  # days
    else:
        raise ValueError("Unsupported time unit. Supported units are 'second', 'minute', 'hour', 'day'.")

    return converted_times
for epoch in ["epoch1","epoch2"]:
    for wave_type in ["lw", "sw"]:
        for rIn in range(10,32,4):
            for rOut in range(30, 65, 10):
                if rOut > rIn:
                    #set up some things:
                    # path = "/Volumes/External Storage/JWST_cal_data/JWST_data_downloaded_20230903/MAST_2023-09-03T1715/JWST/"
                    # path = "/Volumes/External Storage/JWST_cal_data/MAST_2023-02-06T1211/JWST/"
                    path = "T:\MAST_2023-10-07T0548\JWST"            
                    #in flight calculated PSFs for NIRCam - PROBABLY DON'T NEED THIS
                    #https://stsci.app.box.com/v/jwst-simulated-psf-library

                    F070W_canned_PSF_file = './static/lib/PSF_NIRCam_in_flight_opd_filter_F070W.fits'
                    F277W_canned_PSF_file = './static/lib/PSF_NIRCam_in_flight_opd_filter_F277W.fits'

                    F070W_PSF = fits.open(F070W_canned_PSF_file)

                    F070W_PSF_oversampled = F070W_PSF[0] #first extension is the PSF oversampled by 4x relative to detector sampling
                    F070W_PSF_detsampled = F070W_PSF[1]  #second extension is the PSF at detector sampling

                    F277W_PSF = fits.open(F277W_canned_PSF_file)

                    F277W_PSF_oversampled = F277W_PSF[0] #first extension is the PSF oversampled by 4x relative to detector sampling
                    F277W_PSF_detsampled = F277W_PSF[1]  #second extension is the PSF at detector sampling


                    # plt.imshow(F070W_PSF_oversampled.data)
                    # webbpsf.display_psf(F070W_PSF) # use this convenient function to make a nice log plot with labeled axes

                    #bring in the JWST data

                    # sw_files = sorted(glob.glob(path + "jw01666001001*_nrcb1/*crfints.fits"))
                    # lw_files = sorted(glob.glob(path + "jw01666001001*_nrcblong/*crfints.fits"))
                    sw_files = sorted(glob.glob(os.path.join(path, "jw01666001001*_nrcb1", "*crfints.fits")))
                    lw_files = sorted(glob.glob(os.path.join(path, "jw01666001001*_nrcblong", "*crfints.fits")))
                    if epoch == "epoch2":
                        sw_files = sorted(glob.glob(os.path.join(path, "jw01666003001*_nrcb1", "*crfints.fits")))
                        lw_files = sorted(glob.glob(os.path.join(path, "jw01666003001*_nrcblong", "*crfints.fits")))
                        # sw_files = sorted(glob.glob(path + "jw01666003001*_nrcb1/*crfints.fits"))
                        # lw_files = sorted(glob.glob(path + "jw01666003001*_nrcblong/*crfints.fits"))

                    #set up eventual output
                    ap_result = None
                    psf_result = None

                    fileList = lw_files
                    if wave_type == "sw":
                        fileList = sw_files

                    for x in range(len(fileList)):

                        filename = fileList[x]

                        f = fits.open(filename)

                        #important parameters for webbpsf:

                        # detector = f[0].header['DETECTOR']
                        detector = {"NRCB1": "NRCB1", "NRCBLONG": "NRCB5"} #detector name header for LW doesn't actually match with what is accepted by WebbPSF
                        det_x0 = f[0].header['SUBSTRT1'] #Starting pixel in axis 1 direction
                        det_y0 = f[0].header['SUBSTRT2'] #Starting pixel in axis 2 direction
                        subsize1 = f[0].header['SUBSIZE1'] #subarray size in pixels, x direction
                        subsize2 = f[0].header['SUBSIZE2'] #subarray size in pixels, y direction
                        # detector_position = (det_x0 + (subsize1/2), det_y0 + (subsize2/2)) #enables the PSF calculation to be at the center of the subarray

                        #apername = f[0].header['APERNAME'] #name of the aperture

                        filter = f[0].header['FILTER'] #name of the filter

                        #Next, we can calculate the exact spot on the detector where the PSF should be calculated

                        #dictionaries for ease of switching between filters:
                        centers = {"F070W": (83, 85), "F277W": (86, 76), "F322W2": (86,76)} #I've minused 1 from each coord as coords are zero indexed in python but 1 indexed in ds9
                        r = {"F070W": 3, "F277W": 2, "F322W2": 3} #we are going to want to do aperture photometry as well
                        # centers = {"F070W": (83, 85), "F277W": (86, 76)} #I've minused 1 from each coord as coords are zero indexed in python but 1 indexed in ds9
                        # r = {"F070W": 3, "F277W": 2} #we are going to want to do aperture photometry as well
                        # if epoch == "epoch2":
                        #     centers = {"F070W": (83, 85), "F277W": (86, 76), "F322W2": (86,76)} #I've minused 1 from each coord as coords are zero indexed in python but 1 indexed in ds9
                        #     r = {"F070W": 3, "F277W": 2, "F322W2": 3} #we are going to want to do aperture photometry as well
    
                        r_in = rIn
                        r_out = rOut

                        #read in the data
                        data = f["SCI"] #pixel values, in units of surface brightness, for each integration
                        err = f["ERR"] #uncertainty estimates for each pixel, for each integration
                        dq = f["DQ"] #DQ flags for each pixel, for each integration

                        meandata = np.nanmean(data.data, axis=0)
                        x0, y0 = centers[f[0].header["FILTER"]]

                        ap_centroid_mean = centroid_sources(meandata, (x0,), (y0,), box_size=21, centroid_func=centroid_com)
                        ap_xout_mean = ap_centroid_mean[0][0]
                        ap_yout_mean = ap_centroid_mean[1][0]

                        print(filename)
                        print("mean centroid for aperture photometry:", ap_xout_mean, ap_yout_mean)

                        detector_position = (det_x0 + ap_xout_mean, det_y0 + ap_yout_mean) #enables the PSF calculation to be at the center of the subarray

                        #create the PSF:
                        #need to do a bit of investigation here on the best keywords to account for psf position
                        nc = webbpsf.NIRCam()
                        nc.filter = filter
                        nc.detector = detector[f[0].header["DETECTOR"]]
                        nc.detector_position = detector_position
                        # nc.aperturename = apername

                        #psf_grid outputs a psf compatible with photutils
                        psf = nc.psf_grid(num_psfs=1, single_psf_centered=False, all_detectors=False)

                        '''
                        This next bit does an initial aperture photometry run on the mean data, and then uses that flux
                        and the best-fit x,y centroids as input to an initial psf photometry run to calculate an average
                        psf (x,y) for input to the main psf routine.
                        This (hopefully) allieviates the instances where the psf x and y differ significantly from the aperture
                        x and y, which seems to be the case in the LW filter at least.
                        '''

                        #aperture photometry on mean data:

                        bg_aperture_average = CircularAnnulus(((ap_xout_mean, ap_yout_mean)), r_in=r_in, r_out=r_out)
                        aperture_average = CircularAperture(((ap_xout_mean, ap_yout_mean)), r=r[f[0].header["FILTER"]])
                        sigclip_average = SigmaClip(sigma=3.0, maxiters=10)
                        bgstats_average = ApertureStats(meandata, bg_aperture_average, sigma_clip=sigclip_average)
                        apphot_bg_average = bgstats_average.median
                        apphot_bg_err_average = bgstats_average.std
                        npix_average = aperture_average.area_overlap(meandata)

                        ap_out_average = aperture_photometry(meandata, aperture_average)
                        counts_bkgsub_average = ap_out_average["aperture_sum"][0] - (apphot_bg_average*npix_average)
                        #^^^this can now be used as an initial flux for the psf photometry on the mean data

                        #now we can do an initial psf photometry fit to the mean/median data and get an initial psf position
                        fitter = LevMarLSQFitter()
                        fitbox = 11

                        av_pos = Table(names=["x_0", "y_0", "flux_init"], data=[(ap_xout_mean,), (ap_yout_mean,), (counts_bkgsub_average,)])

                        daogroup = SourceGrouper(10) #DAOGroup deprecated, replacing with SourceGrouper
                        photometry = PSFPhotometry(
                            grouper=None, #I don't think we need a grouper because this case only deals with one source, may need to generalize for multiple sources later though
                            localbkg_estimator=None,
                            psf_model=psf,
                            fitter=fitter,
                            fit_shape=(fitbox,fitbox),
                            aperture_radius=r[f[0].header["FILTER"]]
                        )

                        psf_result_average = photometry(data=meandata-apphot_bg_average, init_params=av_pos)

                        psf_xout_mean = psf_result_average["x_fit"][0]
                        psf_yout_mean = psf_result_average["y_fit"][0]

                        print("mean centroid for psf photometry:", psf_xout_mean, psf_yout_mean)

                        #now time to do photometry (both aperture and psf). Loop over full set of exposures:

                        istart = 0 #there is no source in first few frames, this *could* cause a problem. Include them for now.
                        iend = data.data.shape[0]

                        for i in range(istart,iend):
                            print (filename,i)

                            #aperture photometry using (x,y) using average source position:
                            bg_aperture = CircularAnnulus(((ap_xout_mean, ap_yout_mean)), r_in=r_in, r_out=r_out)
                            aperture = CircularAperture(((ap_xout_mean, ap_yout_mean)), r=r[f[0].header["FILTER"]])
                            sigclip = SigmaClip(sigma=3.0, maxiters=10)
                            bgstats = ApertureStats(data.data[i], bg_aperture, mask=dq.data[i] > 0, sigma_clip=sigclip)
                            apphot_bg = bgstats.median
                            apphot_bg_err = bgstats.std
                            npix = aperture.area_overlap(data.data[i], mask=dq.data[i] > 0)

                            ap_out = aperture_photometry(
                                data.data[i], aperture, mask=dq.data[i] > 0, error=err.data[i]
                            )

                            #had a problem in some images where not a single pixel was good. Fix below:
                            if np.isnan(npix) or npix == 0:
                                continue

                            #add some new columns to apphot output
                            ap_out["apphot_bg"] = apphot_bg #average bg per pixel
                            ap_out["apphot_bg_err"] = apphot_bg_err #stdev of bg
                            ap_out["npix"] = npix
                            ap_out["counts_bkgsub"] = ap_out["aperture_sum"] - (ap_out["apphot_bg"]*ap_out["npix"])
                            ap_out["counts_bkgsub_err"] = np.sqrt((ap_out["npix"] * ap_out["apphot_bg_err"]**2) + (ap_out["aperture_sum_err"]**2))


                            #now we can do a rudimentary check for if the source is detected before moving on to psf photometry:
                            #very basic SNR check
                            if ap_out["counts_bkgsub"]/ap_out["counts_bkgsub_err"] < 3:
                                if not psf_result: #this deals with the first image where there is no source and no psf_result
                                    xout = psf_xout_mean
                                    yout = psf_yout_mean
                                else:
                                    xout = np.median(psf_result["x_fit"])
                                    yout = np.median(psf_result["y_fit"])
                                #fix the psf location to the above
                                pos = Table(names=["x_0", "y_0", "flux_init"], data=[(xout,), (yout,), (ap_out["counts_bkgsub"][0],)])
                                psf.x_0.fixed = True
                                psf.y_0.fixed = True
                            else:
                                if not psf_result:
                                    xout = psf_xout_mean
                                    yout = psf_yout_mean
                                else:
                                    xout = np.median(psf_result["x_fit"])
                                    yout = np.median(psf_result["y_fit"])
                                pos = Table(names=["x_0", "y_0", "flux_init"], data=[(xout,), (yout,), (ap_out["counts_bkgsub"][0],)])
                                psf.x_0.fixed = False
                                psf.y_0.fixed = False

                            #now the aperture photometry is sorted, we can move on to PSF photometry

                            bkgrms = MADStdBackgroundRMS()
                            mmm_bkg = MMMBackground(sigma_clip=sigclip)
                            fitter = LevMarLSQFitter()

                            std = bkgrms(data.data[i])
                            bkg = mmm_bkg(data.data[i]) #make sure this is the best estimate of background for PSF
                            #^^^not using this yet but I don't think it makes much difference

                            # print(bkg,apphot_bg)

                            # print("Background RMS:", std)
                            # print("Background:", bkg)

                            daogroup = SourceGrouper(10)
                            photometry = PSFPhotometry( #BasicPSFPhotometry deprecated in photutils 1.9.0, replacing with PSFPhotometry
                                grouper=None,  #I don't think we need a grouper because this case only deals with one source, may need to generalize for multiple sources later though
                                localbkg_estimator=None,
                                psf_model=psf,
                                fitter=fitter,
                                fit_shape=(fitbox,fitbox),
                                aperture_radius=r[f[0].header["FILTER"]]
                            )
                            #experiment using the aperture photometry background for now
                            result_tab = photometry(data=data.data[i]-apphot_bg, init_params=pos, mask=dq.data[i] > 0) #used to be called "image", now it's "data", init_guesses is now init_params

                            #sometimes the psf position fitting really messes up, much like the centering,
                            #let's try and remedy that
                            if np.abs(result_tab['x_fit'][0] - psf_xout_mean) > 2 or np.abs(result_tab['y_fit'][0] - psf_yout_mean) > 2:
                                pos = Table(names=["x_0", "y_0", "flux_init"], data=[(psf_xout_mean,), (psf_yout_mean,), (ap_out["counts_bkgsub"][0],)])
                                psf.x_0.fixed = True
                                psf.y_0.fixed = True
                                result_tab = photometry(data=data.data[i]-apphot_bg, init_params=pos, mask=dq.data[i] > 0)

                            if psf.x_0.fixed:
                                result_tab["x_err"] = 0.0 #used to be called x_fit_unc
                                result_tab["y_err"] = 0.0

                            #now I think it's time to investigate the true uncertainties on the data
                            #most of the below is from D. Kaplan
                            result_copy = copy.deepcopy(result_tab)
                            result_copy["flux_fit"] = 1
                            residual_image = photometry.make_residual_image(data.data[i],(fitbox,fitbox)) #get_residual_image is now "make_residual_image"

                            #create a cutout of the source around the fitbox
                            slice = np.s_[
                                int(result_tab["y_fit"][0]) - fitbox // 2 : int(result_tab["y_fit"][0]) + fitbox // 2 + 1,
                                int(result_tab["x_fit"][0]) - fitbox // 2 : int(result_tab["x_fit"][0]) + fitbox // 2 + 1,
                            ]

                            diff = residual_image[slice]
                            diff_err = err.data[i][slice]
                            # chisq = ((diff / diff_err) ** 2).sum()
                            chisq = nansumwrapper((diff / diff_err) ** 2)
                            # the normal PSF subtraction has mysterious error analysis
                            # so we will repeat it here such that we can track the statistics
                            # first make a PSF image.  This may not be the easiest way but we will subtract the PSF from
                            # an image that is all 0 and flip it.
                            # then assume that the previous fit got the position right, so only fit for the
                            # flux.  That can be done with linear chi^2
                            # so the flux and flux_err behave well.
                            # save those results too for comparison
                            im = data.data[i][slice] - apphot_bg
                            # psf_image = -photutils.psf.utils.subtract_psf(data.data[i] * 0, psf, result_copy)

                            #this code is directly lifted from the source code for subtract_psf, which is now deprecated https://photutils.readthedocs.io/en/1.11.0/_modules/photutils/psf/utils.html#subtract_psf
                            #-----------------------------------------
                            indices = np.indices(data.data[i].shape)
                            psf_image = data.data[i] * 0
                            indices_reversed = indices[::-1]
                            for row in result_copy:
                                getattr(psf, "x_0").value = row['x_fit']
                                getattr(psf, "y_0").value = row['y_fit']
                                getattr(psf, "flux").value = row['flux_fit']

                                psf_image += psf(*indices_reversed)
                            #------------------------------------------
                            # psf_image = photometry.make_model_image(data.data[i].shape,(fitbox,fitbox))

                            # flux = (im * psf_image[slice] / err.data[i][slice] ** 2).sum() / (
                            #     psf_image[slice] ** 2 / err.data[i][slice] ** 2
                            # ).sum()
                            flux = nansumwrapper((im * psf_image[slice] / err.data[i][slice] ** 2)) / nansumwrapper((
                                psf_image[slice] ** 2 / err.data[i][slice] ** 2
                            ))
                            # flux_err = np.sqrt(1 / (psf_image[slice] ** 2 / err.data[i][slice] ** 2).sum())
                            flux_err = np.sqrt(1 / nansumwrapper((psf_image[slice] ** 2 / err.data[i][slice] ** 2)))
                            # chisqb = (((im - flux * psf_image[slice]) / err.data[i][slice]) ** 2).sum()
                            chisqb = nansumwrapper((((im - flux * psf_image[slice]) / err.data[i][slice]) ** 2))

                            result_tab["chisq"] = chisq
                            result_tab["chisq_v2"] = chisqb
                            if psf.x_0.fixed:
                                result_tab["dof"] = (fitbox**2) - 1 #psf fits flux only in this case so minus 1 from no. of pixels in cutout for dof
                            else:
                                result_tab["dof"] = (fitbox**2) - 3 #psf fits flux, x and y, so minus 3 from no. of pixels in cutout for dof
                            result_tab["flux_recalc"] = flux
                            result_tab["flux_recalc_unc"] = flux_err

                            #now we have all our flux and uncertainty data, let's extract the time data from the frame

                            t = Time(f["INT_TIMES"].data["int_mid_BJD_TDB"][i], format="mjd", scale="tdb")
                            exptime = (
                                f["INT_TIMES"].data["int_end_BJD_TDB"] - f["INT_TIMES"].data["int_start_BJD_TDB"]
                            )[i] * u.d

                            #and the filename (removing the long path)

                            fname = f[0].header["FILENAME"]

                            # ap_out["int_mid_BJD_TDB"] = t.mjd
                            # ap_out["dT"] = exptime.to(u.s)

                            #now we have every relevant piece of info, let's output it.
                            #going to take David's advice and use astropy tables and hdf5 output files
                            #(easier to add columns later when we change the code to work out uncertainties)

                            if ap_result is None:
                                ap_result = Table(
                                    names=[
                                        "frame",
                                        "int_mid_BJD_TDB",
                                        "dT",
                                        "filename",
                                        "xcenter",
                                        "ycenter",
                                        "aperture_sum",
                                        "aperture_sum_err",
                                        "bg",
                                        "bg_err",
                                        "npix",
                                        "counts_bkgsub",
                                        "counts_bkgsub_err"

                                    ],
                                    data=[
                                        (i+1,),
                                        (t.mjd,),
                                        (exptime.to(u.s),),
                                        (fname,),
                                        (ap_out["xcenter"][0],),
                                        (ap_out["ycenter"][0],),
                                        (ap_out["aperture_sum"][0],),
                                        (ap_out["aperture_sum_err"][0],),
                                        (ap_out["apphot_bg"][0],),
                                        (ap_out["apphot_bg_err"][0],),
                                        (ap_out["npix"][0],),
                                        (ap_out["counts_bkgsub"][0],),
                                        (ap_out["counts_bkgsub_err"][0],),
                                    ],
                                )
                            else:
                                row = [ap_out[0][c] for c in ap_out.colnames[1:]]
                                ap_result.add_row([i+1, t.mjd, exptime.to(u.s), fname]  + row)

                            #now write out the psf results:
                            # print(i, ap_out)
                            # print(i, result_tab)

                            #delete id and group id from table, it is useless data
                            # result_tab.remove_columns(['id','group_id'])
                            #loads more useless columns in this new version of photutils
                            result_tab.remove_columns(['id','group_id','local_bkg','npixfit', 'group_size', 'qfit', 'cfit', 'flags'])

                            #sometimes the psf fit just plain doesn't work even after everything, in which case just skip the row?
                            if len(result_tab[0]) < 14:
                                continue
                            
                            if psf_result is None:
                                psf_result = Table(
                                    names=[
                                        "frame",
                                        "int_mid_BJD_TDB",
                                        "dT",
                                        "filename",
                                        "x_0",
                                        "y_0",
                                        "flux_init",
                                        "x_fit",
                                        "y_fit",
                                        "flux_fit",
                                        "x_fit_unc",
                                        "y_fit_unc",
                                        "flux_unc",
                                        "chisq",
                                        "chisq_v2",
                                        "dof",
                                        "flux_recalc",
                                        "flux_recalc_unc",
                                    ],
                                    data=[
                                        (i+1,),
                                        (t.mjd,),
                                        (exptime.to(u.s),),
                                        (fname,),
                                        (result_tab["x_init"][0],),
                                        (result_tab["y_init"][0],),
                                        (result_tab["flux_init"][0],),
                                        (result_tab["x_fit"][0],),
                                        (result_tab["y_fit"][0],),
                                        (result_tab["flux_fit"][0],),
                                        (result_tab["x_err"][0],),
                                        (result_tab["y_err"][0],),
                                        (result_tab["flux_err"][0],),
                                        (result_tab["chisq"][0],),
                                        (result_tab["chisq_v2"][0],),
                                        (result_tab["dof"][0],),
                                        (result_tab["flux_recalc"][0],),
                                        (result_tab["flux_recalc_unc"][0],),
                                    ],
                                )
                            else:
                                row = [result_tab[0][c] for c in result_tab.colnames]
                                psf_result.add_row([i+1, t.mjd, exptime.to(u.s), fname]  + row)
                    
                    T0 = Time(59341.9957698098, format="mjd", scale="tdb")
                    P = 414.78942014 * u.s
                    Pdot = -2.362e-11 * u.s / u.s
                    F = 1 / P
                    Fdot = -Pdot / P**2
                    should_sort_data = True
                    psf_time = np.array(psf_result['int_mid_BJD_TDB'])
                    psf_flux = np.array(psf_result['flux_recalc'])
                    psf_flux_unc = np.array(psf_result['flux_recalc_unc'])
                    psf_chi = np.array(psf_result['chisq_v2'])
                    psf_dof = np.array(psf_result['dof'])
                    psf_frame = np.array(psf_result['frame'])
                    psf_fits_file_name = np.array(psf_result['filename'])
                    red_chi2 = np.array([chi / dof for chi, dof in zip(psf_chi, psf_dof)])
                    psf_time = psf_time[np.where(
                        red_chi2 < 1.0 if wave_type == 'sw' else red_chi2 < 2.0)]
                    psf_flux = psf_flux[np.where(
                        red_chi2 < 1.0 if wave_type == 'sw' else red_chi2 < 2.0)]
                    psf_flux_unc = psf_flux_unc[np.where(
                        red_chi2 < 1.0 if wave_type == 'sw' else red_chi2 < 2.0)]
                    psf_frame = psf_frame[np.where(
                        red_chi2 < 1.0 if wave_type == 'sw' else red_chi2 < 2.0)]
                    psf_fits_file_name = psf_fits_file_name[np.where(red_chi2 < 1.0 if wave_type == 'sw' else red_chi2 < 2.0)]
                    t = Time(psf_time, format="mjd", scale="tdb")
                    dt = t - T0
                    phase = (F * dt + 0.5 * Fdot * dt * dt).decompose()
                    # if should_sort_data:
                    #     sorted_indices = sorted(range(len(phase)), key=lambda k: phase[k].value % 1)
                    #     phase_sorted_temp = [phase[i] for i in sorted_indices]
                    #     psf_flux_sorted_temp = [psf_flux[i] for i in sorted_indices]
                    #     psf_flux_unc_sorted_temp = [psf_flux_unc[i] for i in sorted_indices]
                    # else:                
                    #     phase_sorted_temp = phase
                    #     psf_flux_sorted_temp = psf_flux
                    #     psf_flux_unc_sorted_temp = psf_flux_unc
                    # phase_values_sorted_temp = [phase.value % 1 for phase in phase_sorted_temp]

                    time_mjd = np.array([time.mjd for time in np.array(t)])
                    time_second = convert_time_units(np.array(time_mjd), 'second')
                    time_minute = convert_time_units(np.array(time_mjd), 'minute')
                    time_hour = convert_time_units(np.array(time_mjd), 'hour')
                    time_day = convert_time_units(np.array(time_mjd), 'day')
                    phase_values = [p.value % 1 for p in phase]
                    psf_flux_time = psf_flux
                    psf_flux_unc_time = psf_flux_unc
                    frame = np.array(psf_frame)
                    fits_file_name = np.array(psf_fits_file_name)
                    customdata_time = np.array([{'mjd': mjd, 'phase': phase} for mjd, phase in zip(time_mjd, phase_values)])

                    sorted_indices = sorted(range(len(phase)), key=lambda k: phase[k].value % 1)
                    phase_sorted = [phase[i] for i in sorted_indices]
                    phase_values_sorted = [p.value % 1 for p in phase_sorted]
                    time_sorted = [time_mjd[i] for i in sorted_indices]
                    psf_flux_sorted = [psf_flux[i] for i in sorted_indices]
                    psf_flux_unc_sorted = [psf_flux_unc[i] for i in sorted_indices]
                    frame_sorted = [frame[i] for i in sorted_indices]
                    fits_file_name_sorted = [fits_file_name[i] for i in sorted_indices]
                    customdata_phase = np.array([{'mjd': mjd, 'phase': phase} for mjd, phase in zip(time_sorted, phase_values_sorted)])

                    # psf_flux_phase = np.concatenate((psf_flux_sorted, psf_flux_sorted))
                    # psf_flux_unc_phase = np.concatenate((psf_flux_unc_sorted, psf_flux_unc_sorted))
                    # frame_phase = np.concatenate((frame_sorted, frame_sorted))
                    # phase_values_phase = np.concatenate((np.array(phase_values_sorted), np.array(phase_values_sorted) + 1))

                    # valid_mask = ~np.isnan(psf_flux_sorted_temp)
                    # computed_psf = {
                    #     'psf_flux_sorted': np.array(psf_flux_sorted_temp)[valid_mask],
                    #     'psf_flux_unc_sorted': np.array(psf_flux_unc_sorted_temp)[valid_mask],
                    #     'time_sorted': np.array([time.mjd for time in np.array(time_sorted_temp)[valid_mask]]),
                    #     'phase_values_sorted': np.array(phase_values_sorted_temp)[valid_mask],
                    #     'time_values_sorted': np.array([time.value for time in np.array(time_sorted_temp)[valid_mask]]),
                    # }
                    customdata_time_json = np.array([json.dumps(item) for item in customdata_time], dtype=str)
                    customdata_phase_json = np.array([json.dumps(item) for item in customdata_phase], dtype=str)
                    computed_psf = {
                        'time': np.array(time_mjd),
                        'time_second': np.array(time_second),
                        'time_minute': np.array(time_minute),
                        'time_hour': np.array(time_hour),
                        'time_day': np.array(time_day),
                        'phase_values': np.array(phase_values),
                        'psf_flux_time': np.array(psf_flux_time),
                        'psf_flux_unc_time': np.array(psf_flux_unc_time),
                        'frame': np.array(frame),
                        'fits_file_name': np.array(fits_file_name),
                        'customdata_time': np.array(customdata_time_json),

                        # 'phase_sorted': np.array(phase_sorted),
                        'phase_values_sorted': np.array(phase_values_sorted),
                        'time_sorted': np.array(time_sorted),
                        'psf_flux_sorted': np.array(psf_flux_sorted),
                        'psf_flux_unc_sorted': np.array(psf_flux_unc_sorted),
                        'frame_sorted': np.array(frame_sorted),
                        'fits_file_name_sorted': np.array(fits_file_name_sorted),
                        'customdata_phase': np.array(customdata_phase_json),

                        # 'psf_flux_phase': np.array(psf_flux_phase),
                        # 'psf_flux_unc_phase': np.array(psf_flux_unc_phase),
                        # 'frame_phase': np.array(frame_phase),
                        # 'phase_values_phase': np.array(phase_values_phase)
                    }
                    # for key, value in computed_psf.items():
                    #     print(f'Length of {key}: {len(value)}')
                    computed_psf_table = Table(computed_psf)

                    # ap_result.write(
                    #     f"Shaw_ZTF_J1539_photometry_LW.experimental.hdf5", overwrite=True, serialize_meta=True, path="aperture"
                    # )

                    # psf_result.write(
                    #     f"Shaw_ZTF_J1539_photometry_SW.experimental.hdf5", append=True, overwrite=True, serialize_meta=True, path="psf"
                    # )

                    id = f"{epoch}_{wave_type}_{r_in}_{r_out}"
                    combined_dict = {
                        "_id":id,
                        "code": "ZTF_J1539",
                        "type": wave_type,
                        "r_in": r_in,
                        "r_out": r_out,
                        "epoch":epoch,
                        "aperture": {
                                    "frame": ap_result["frame"].tolist(),
                                    "int_mid_BJD_TDB": ap_result["int_mid_BJD_TDB"].tolist(),
                                    "dT": ap_result["dT"].tolist(),
                                    "filename": ap_result["filename"].tolist(),
                                    "xcenter": ap_result["xcenter"].tolist(),
                                    "ycenter": ap_result["ycenter"].tolist(),
                                    "aperture_sum": ap_result["aperture_sum"].tolist(),
                                    "aperture_sum_err": ap_result["aperture_sum_err"].tolist(),
                                    "bg": ap_result["bg"].tolist(),
                                    "bg_err": ap_result["bg_err"].tolist(),
                                    "npix": ap_result["npix"].tolist(),
                                    "counts_bkgsub": ap_result["counts_bkgsub"].tolist(),
                                    "counts_bkgsub_err": ap_result["counts_bkgsub_err"].tolist(),
                        },
                        "psf": {
                                "frame": psf_result["frame"].tolist(),
                                "int_mid_BJD_TDB": psf_result["int_mid_BJD_TDB"].tolist(),
                                "dT": psf_result["dT"].tolist(),
                                "filename": psf_result["filename"].tolist(),
                                "x_0": psf_result["x_0"].tolist(),
                                "y_0": psf_result["y_0"].tolist(),
                                "flux_init": psf_result["flux_init"].tolist(),
                                "x_fit": psf_result["x_fit"].tolist(),
                                "y_fit": psf_result["y_fit"].tolist(),
                                "flux_fit": psf_result["flux_fit"].tolist(),
                                "x_fit_unc": psf_result["x_fit_unc"].tolist(),
                                "y_fit_unc": psf_result["y_fit_unc"].tolist(),
                                "flux_unc": psf_result["flux_unc"].tolist(),
                                "chisq": psf_result["chisq"].tolist(),
                                "chisq_v2": psf_result["chisq_v2"].tolist(),
                                "dof": psf_result["dof"].tolist(),
                                "flux_recalc": psf_result["flux_recalc"].tolist(),
                                "flux_recalc_unc": psf_result["flux_recalc_unc"].tolist(),
                        },
                        "computed_psf": {
                            'time': computed_psf_table["time"].tolist(),
                            'time_second': computed_psf_table["time_second"].tolist(),
                            'time_minute': computed_psf_table["time_minute"].tolist(),
                            'time_hour': computed_psf_table["time_hour"].tolist(),
                            'time_day': computed_psf_table["time_day"].tolist(),
                            'phase_values': computed_psf_table["phase_values"].tolist(),
                            'psf_flux_time': computed_psf_table["psf_flux_time"].tolist(),
                            'psf_flux_unc_time': computed_psf_table["psf_flux_unc_time"].tolist(),
                            'frame': computed_psf_table["frame"].tolist(),
                            'fits_file_name': computed_psf_table["fits_file_name"].tolist(),
                            'customdata_time': computed_psf_table["customdata_time"].tolist(),

                            # 'phase_sorted': computed_psf_table["phase_sorted"].tolist(),
                            'phase_values_sorted': computed_psf_table["phase_values_sorted"].tolist(),
                            'time_sorted': computed_psf_table["time_sorted"].tolist(),
                            'psf_flux_sorted': computed_psf_table["psf_flux_sorted"].tolist(),
                            'psf_flux_unc_sorted': computed_psf_table["psf_flux_unc_sorted"].tolist(),
                            'frame_sorted': computed_psf_table["frame_sorted"].tolist(),
                            'fits_file_name_sorted': computed_psf_table["fits_file_name_sorted"].tolist(),
                            'customdata_phase': computed_psf_table["customdata_phase"].tolist(),

                            # 'psf_flux_phase': computed_psf_table["psf_flux_phase"].tolist(),
                            # 'psf_flux_unc_phase': computed_psf_table["psf_flux_unc_phase"].tolist(),
                            # 'frame_phase': computed_psf_table["frame_phase"].tolist(),
                            # 'phase_values_phase': computed_psf_table["phase_values_phase"].tolist()
                        }
                        }
                        
                    id = collection.insert_one(combined_dict).inserted_id
                    pprint.pprint(collection.find_one())


                    ap_result.write(
                        f"T:\jwst\static\data\Shaw_ZTF_J1539_photometry."+str(epoch)+"."+str(wave_type)+"."+str(r_in)+"."+str(r_out)+".hdf5", overwrite=True, serialize_meta=True, path="aperture"
                    )

                    psf_result.write(
                        f"T:\jwst\static\data\Shaw_ZTF_J1539_photometry."+str(epoch)+"."+str(wave_type)+"."+str(r_in)+"."+str(r_out)+".hdf5", append=True, overwrite=True, serialize_meta=True, path="psf"
                    )

                    computed_psf_table.write(
                        f"T:\jwst\static\data\Shaw_ZTF_J1539_photometry."+str(epoch)+"."+str(wave_type)+"."+str(r_in)+"."+str(r_out)+".hdf5", append=True, overwrite=True, serialize_meta=True, path="computed_psf"
                    )
                    
                    print("Time taken to run (s):", time.process_time())
