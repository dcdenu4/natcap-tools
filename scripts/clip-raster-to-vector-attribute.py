import os
import sys
import logging
import argparse

from osgeo import gdal, osr, ogr

import pygeoprocessing
import taskgraph

logging.basicConfig(
    level=logging.DEBUG,
    format=(
        '%(asctime)s (%(relativeCreated)d) %(levelname)s %(name)s'
        ' [%(funcName)s:%(lineno)d] %(message)s'),
    stream=sys.stdout)
LOGGER = logging.getLogger(__name__)

def clip_raster_to_vector_feature(
        input_raster_path, input_vector_path, output_raster_path,
        field_name, field_value, working_dir):
    """Clips a raster from a vector.

    Args:
        input_raster_path (string): path to a GDAL vector file.
        input_vector_path (string): path to a GDAL vector file.
        output_raster_path (string):
        field_name (string):
        field_value (string):
        working_dir (string):

    Returns:
        None
    """

    unique_field_names = get_unique_vector_attributes(
        input_vector_path, input_raster_path, field_name)

    unique_dict = dict(unique_field_names)

    raster_info = pygeoprocessing.get_raster_info(input_raster_path)
    input_vector = gdal.OpenEx(input_vector_path, gdal.OF_VECTOR)
    input_layer = input_vector.GetLayer(0)

    feature = input_layer.GetFeature(unique_dict[field_value])
    feature_geom = feature.GetGeometryRef()
    envelope = feature_geom.GetEnvelope()
    feature_bb = [envelope[i] for i in [0, 2, 1, 3]]
    feature = None
    input_layer = None
    input_vector = None

    # Protect against the clipping feature bb being outside the extents of 
    # the raster.
    target_bb = pygeoprocessing.merge_bounding_box_list(
        [feature_bb, raster_info['bounding_box']], 'intersection')

    vector_options = {
        'mask_vector_path': input_vector_path,
        'mask_vector_where_filter':f"{field_name}='{field_value}'"
    }

    pygeoprocessing.align_and_resize_raster_stack(
        [input_raster_path], [output_raster_path], ['near'],
        raster_info['pixel_size'], target_bb,
        vector_mask_options=vector_options)

def get_unique_vector_attributes(
        input_vector_path, input_raster_path, field_name):
    """Return a list of unique values from the vector features field.

    Only return the values if the feature geometry intersects the raster.

    Args:
        input_vector_path (string): path to a GDAL vector file.
        input_raster_path (string): path to a GDAL raster file.
        field_name (string): attribute name to be compiled into list.

    Returns:
        A unique list of values.
    """
    LOGGER.debug(f"Get unique feature attributes.")

    raster_info = pygeoprocessing.get_raster_info(input_raster_path)
    input_vector = gdal.OpenEx(input_vector_path, gdal.OF_VECTOR)
    input_layer = input_vector.GetLayer(0)

    unique_list = []
    for feat in input_layer:
        feat_fid = feat.GetFID()
        feat_value = feat.GetFieldAsString(field_name)

        feature_geom = feat.GetGeometryRef()
        envelope = feature_geom.GetEnvelope()
        feature_bb = [envelope[i] for i in [0, 2, 1, 3]]

        if feat_value not in unique_list:
            try:
                target_bb = pygeoprocessing.merge_bounding_box_list(
                    [feature_bb, raster_info['bounding_box']], 'intersection')
                unique_list.append((feat_value, feat_fid))
            except ValueError:
                LOGGER.info(
                    f'Bounding box with raster and polygon did not overlap.'
                    f' {feat_value} and {input_raster_path}')

        feat = None

    input_layer = None
    input_vector = None

    return unique_list


if __name__ == "__main__":

    LOGGER.debug("Starting Raster Clip Processing")

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--raster',
        help="The input raster to clip.", required=True)
    parser.add_argument('-v', '--vector',
        help="The input vector to clip from.", required=True)
    parser.add_argument('-f', '--field',
        help="The input vector field to use for clipping.", required=True)
    parser.add_argument('-fv', '--value',
        help="The input vector field value to use for clipping.", required=True)
    parser.add_argument('-d', '--dst',
            help="The clipped output raster path.", required=True)

    args = vars(parser.parse_args())

    out_path = args['dst']
    out_dir = os.path.dirname(out_path)


    LOGGER.info(f"raster : {args['raster']}")
    LOGGER.info(f"vector : {args['vector']}")
    LOGGER.info(f"field : {args['field']}")
    LOGGER.info(f"dst : {args['dst']}")

    LOGGER.info(f"out_dir : {out_dir}")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    ### TaskGraph Set Up
    taskgraph_working_dir = os.path.join(
        out_dir, '_clip_raster_tg_working_dir')

    n_workers = -1
    task_graph = taskgraph.TaskGraph(taskgraph_working_dir, n_workers)
    ###

    clip_task = task_graph.add_task(
        func=clip_raster_to_vector_feature,
        args=(
            args['raster'], args['vector'], out_path, args['field'],
            args['value'], taskgraph_working_dir),
        target_path_list=[out_path],
        task_name=f'clip_raster_task')

    LOGGER.info("Finished Clipping Raster")
