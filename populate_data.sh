#!/bin/bash

mkdir -p data && cd data
wget https://www.weather.gov/source/gis/Shapefiles/County/c_05mr24.zip
wget https://prd-tnm.s3.amazonaws.com/StagedProducts/Small-scale/data/Boundaries/countyl010g_shp_nt00964.tar.gz

tar zxvf countyl010g_shp_nt00964.tar.gz
rm *tar.gz *xml
