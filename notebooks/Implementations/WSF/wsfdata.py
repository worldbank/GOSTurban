import rasterio
import pandas as pd
import numpy as np


class wsf_dataset(object):
    def __init__(self, imageList):
        """Create object organizning and analyzing WSF data.

        INPUT
            imageList [array of strings] - list of paths to input images
        """
        for img in imageList:
            if "AW3D30.tif" in img:
                self.heightImg = img
            if "AW3D30_nScenes.tif" in img:
                self.heightImg_nScenes = img
            if "WSFevolution.tif" in img:
                self.evolution = img
            if "WSFevolution_IDCscore.tif" in img:
                self.evolution_idc = img

    def analyze_idc(self, outFile="", badThreshold=2):
        """Analyze the IDC (quality) image

        INPUT
            [optional] outfile [string] - path to create output file describing quality
            [optional] badThreshold [number] - values above this will be considered low quality
        RETURNS
            [numpy array] - 2band np array of same size as the input IDC image.
                Band 1 - Total number of years with bad data
                Band 2 - Most recent year of bad data
        """
        idc = rasterio.open(self.evolution_idc)
        idcD = idc.read()
        # Analyze the IDC dataset and write the results to file
        outArray = np.zeros([2, idcD.shape[1], idcD.shape[2]])
        for rIdx in range(0, idcD.shape[2]):
            for cIdx in range(0, idcD.shape[1]):
                curD = idcD[:, cIdx, rIdx]
                notGood = curD > badThreshold
                try:
                    newestBadYear = max([i for i, x in enumerate(notGood) if x])
                except:
                    newestBadYear = 0
                outArray[0, cIdx, rIdx] = notGood.sum()
                outArray[1, cIdx, rIdx] = newestBadYear
        if outFile != "":
            # Write the summary dataset to file
            ### BAND 1 - total number of bad years
            ### BAND 2 - most recent bad year
            outProfile = idc.profile.copy()
            outProfile.update(count=2)
            with rasterio.open(outFile, "w", **outProfile) as outData:
                outData.write(outArray.astype(outProfile["dtype"]))
                outData.set_band_description(1, "TotalBadYears")
                outData.set_band_description(2, "MostRecentBad")
        self.quality_summary = outArray
        return outArray.astype(idc.profile["dtype"])

    def correct_evolution_idc(self, outfile="", badThreshold=2):
        """Correct the WSF evolution dataset based on quality flags. This is done by changing
            the WSF built date if the quality flag is worse than badThreshold. If it is worse,
            the cell is assigned the next date in the WSF quality flag that is of acceptable quality.

        INPUT
            [optional] outfile [string] - path to create output file with corrected evolution dataset
            [optional] badThreshold [number] - values above this will be considered low quality
        RETURNS
            [numpy array] - np array of same size as the input evolution image.
        """
        inEvolution = rasterio.open(self.evolution)
        inIDC = rasterio.open(self.evolution_idc)
        inE = inEvolution.read()
        inD = inIDC.read()
        outArray = np.zeros(inE.shape)
        for rIdx in range(0, inE.shape[2]):
            for cIdx in range(0, inE.shape[1]):
                curE = inE[0, cIdx, rIdx]
                curD = inD[:, cIdx, rIdx]
                if curE > 0:
                    qualityIdx = curE - 1985
                    if curD[qualityIdx] > badThreshold:
                        for xIdx in range(0, len(curD)):
                            if xIdx > qualityIdx:
                                if curD[xIdx + 1] <= badThreshold:
                                    break
                            curE = 1985 + xIdx
                inE[0, cIdx, rIdx] = curE
        if outfile != "":
            # Write the corrected evolution dataset to file
            outProfile = inEvolution.profile.copy()
            with rasterio.open(outfile, "w", **outProfile) as outData:
                outData.write(inE.astype(outProfile["dtype"]))
        return inE

    def generate_evolution_plot(self, dataset="normal"):
        """generate a dataframe for matplotlib plotting

        INPUT
        [optional] dataset [pandas dataframe] - provide a dataset to analyze,
            if you don't want to read in the evolution dataset

        RETURNS
        [geopandas dataframe]

        EXAMPLE
        wsfD = wsfdata.wsf_dataset(images_list)
        basePlot = wsfD.generate_evolution_plot()
        # generate corrected data
        correctedRes = wsfD.correct_evolution_idc(badThreshold=3)
        correctedPlot = wsfD.generate_evolution_plot(dataset=correctedRes)
        basePlot['corrected'] = correctedPlot['cumBuilt']

        basePlot.drop('built', axis=1).plot()

        basePlot['cumBuilt'].plot()
        """
        if dataset == "normal":
            evolution = rasterio.open(self.evolution)
            inD = evolution.read()
        else:
            inD = dataset
        unique, counts = np.unique(inD, return_counts=True)
        res = pd.DataFrame(counts, unique).drop(0)
        res.columns = ["built"]
        missingDates = [x for x in range(1985, 2015) if x not in res.index]
        for x in missingDates:
            res.loc[x] = 0
        res = res.sort_index()
        res["cumBuilt"] = res["built"].cumsum()
        return res

    def summarize_idc(self, thresh):
        """Summarize IDC by measuring what percentage of the built cells in every
            year are above the defined quality threshold

        INPUT
        thresh [number] - value from 1-6 defining the acceptable quality threshold, every value
            below or equal to that threshold (better than that value) are considered acceptable

        RETURNS
        [numpy array] - fraction of built cells that are of acceptable quality per year. HOPEFULLY
            the reutrning array should be 31 records long
        """
        idc = rasterio.open(self.evolution_idc).read()
        evolution = rasterio.open(self.evolution).read()

        evolution_mask = idc.copy() * 0
        evolution_mask[:, :, :] = evolution[0, :, :] == 0
        evolution_masked = np.ma.array(idc, mask=evolution_mask[np.newaxis, :, :])

        totalCells = (evolution[0, :, :] > 0).sum()
        allRes = []
        for idx in range(0, evolution_masked.shape[0]):
            allRes.append((evolution_masked[idx, :, :] > thresh).sum() / totalCells)

        return allRes
