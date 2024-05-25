import sys
import os
import shutil
import requests
import rasterio


import GOSTurban.UrbanRaster as urban


def download_pop_file(url, filename):
    # Open the url
    r = requests.get(url)
    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    r.raw.decode_content = True
    # Open a local file with wb ( write binary ) permission.
    with open(filename, "wb") as f:
        shutil.copyfileobj(r.raw, f)


def main(iso3, out_folder):
    # download the population data
    wp_url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/{iso3.upper()}/{iso3.lower()}_ppp_2020_1km_Aggregated.tif"
    print(wp_url)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    out_file = os.path.join(out_folder, f"{iso3}_ppp_2020_1km_Aggregated.tif")
    out_urban = os.path.join(out_folder, "urban_extents.geojson")
    out_hd_urban = os.path.join(out_folder, "hd_urban_extents.geojson")

    try:
        if not os.path.exists(out_file):
            download_pop_file(wp_url, out_file)
    except:
        print(f"Could not download national population data for {iso3} from {wp_url}")
        print(
            "If you can manually download to the defined out_folder, the script will run"
        )
    if os.path.exists(out_file):
        inR = rasterio.open(out_file)
        urban_calculator = urban.urbanGriddedPop(inR)
        urban_extents = urban_calculator.calculateUrban(
            densVal=300, totalPopThresh=5000, smooth=False, queen=False
        )

        hd_urban_extents = urban_calculator.calculateUrban(
            densVal=1500,
            totalPopThresh=50000,
            smooth=True,
            queen=True,  # high density extents use queen's case contiguity, and are smoothed
        )

        urban_extents.to_file(out_urban, driver="GeoJSON")
        hd_urban_extents.to_file(out_hd_urban, driver="GeoJSON")


if __name__ == "__main__":
    iso3 = sys.argv[1]
    out_folder = sys.argv[2]
    main(iso3, out_folder)
