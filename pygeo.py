import argparse
import os
import logging
import sys

import numpy
import pygeoprocessing

logging.basicConfig(
    level=logging.DEBUG,
    format=(
        '%(asctime)s (%(relativeCreated)d) %(levelname)s %(name)s'
        ' [%(funcName)s:%(lineno)d] %(message)s'),
    stream=sys.stdout)
LOGGER = logging.getLogger(__name__)

def define_nodata(raster_path, output_path, nodata_value):
    """Copies a raster and sets the output nodata value."""

    def _identity_op(array):

        return array

    raster_info = pygeoprocessing.get_raster_info(raster_path)
    pygeoprocessing.raster_calculator(
        [(raster_path, 1)], _identity_op, output_path, raster_info['datatype'],
        nodata_value)

def nodata_to_value(raster_path, output_path, nodata, out_value):
    """Copies a raster and sets nodata to a new value non nodata value."""

    raster_info = pygeoprocessing.get_raster_info(raster_path)
    LOGGER.info("nodata: ", raster_info['nodata'][0])

    def _replace_nodata_op(array):

        out_array = numpy.where(
                        array==raster_info['nodata'][0], out_value, array)

        return out_array

    pygeoprocessing.raster_calculator(
        [(raster_path, 1)], _replace_nodata_op, output_path,
        raster_info['datatype'], nodata)

def change_nodata(raster_path, output_path, out_nodata):
    """Copies a raster and changes nodata to a new nodata value."""

    raster_info = pygeoprocessing.get_raster_info(raster_path)
    nodata = raster_info['nodata'][0]
    LOGGER.info(f"nodata: {nodata}")

    def _change_nodata_op(array):
        result = numpy.full_like(array, out_nodata)
        valid_mask = ~numpy.isclose(array, nodata, equal_nan=True)
        result[valid_mask] = array[valid_mask]

        return result

    pygeoprocessing.raster_calculator(
        [(raster_path, 1)], _change_nodata_op, output_path,
        raster_info['datatype'], out_nodata)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        help = "The operation to perform"
               " {define-nodata | nodata-to-value | change-nodata}"
    )

    parser.add_argument("--src", help = "Path to the source input.")
    parser.add_argument("--dst", help = "Path to the generated output.")
    parser.add_argument("--nodata", help = "The nodata value.")
    parser.add_argument("--new-value", help = "Value to replace nodata.")

    args = vars(parser.parse_args())

    if args['operation'] == 'define-nodata':
        try:
            define_nodata(args['src'], args['dst'], int(args['nodata']))
        except:
            LOGGER.debug(args)
            raise

    elif args['operation'] == 'nodata-to-value':
        try:
            nodata_to_value(
                args['src'], args['dst'], float(args['nodata']),
                float(args['new_value']))
        except:
            LOGGER.debug(args)
            raise
    elif args['operation'] == 'change-nodata':
        try:
            change_nodata(
                args['src'], args['dst'], float(args['new_value']))
        except:
            LOGGER.debug(args)
            raise
    else:
        LOGGER.info("Not an operation")
