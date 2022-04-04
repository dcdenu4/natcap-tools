import argparse
import os
import numpy

from osgeo import gdal
from osgeo import osr

import pygeoprocessing


def replace_raster_value(file_path, file_out_path, value, replace_value):
    """ """
    raster_info = pygeoprocessing.get_raster_info(file_path)
    def replace_op(orig_values):
        mask = orig_values == value
        return numpy.where(mask, replace_value, orig_values)

    print(raster_info)
    pygeoprocessing.raster_calculator([(file_path, 1)], replace_op, 
            file_out_path, raster_info['datatype'], raster_info['nodata'][0])



if __name__ == "__main__":
    # execute only if run as a script

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file")
    parser.add_argument("-fo", "--file-out")
    parser.add_argument("-vi", "--val-in", type=int)
    parser.add_argument("-vo", "--val-out", type=int)

    args = parser.parse_args()
    print(vars(args))
    print(*list(vars(args).values()))
    
    replace_raster_value(*list(vars(args).values()))
