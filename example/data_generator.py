"""Generates GIS data for use in testing."""

from os import path

import arcpy


def create_gdb(gdb_path, path_json_file,
               conus_json_file=None):
    """Create and populate an Esri file geodatabase with path features.

    Add these features to a map and use them for testing or demonstration.

    Args:
        gdb_path: Path and name of target geodatabase, e.g., c:\work\data.gdb
        path_json_file: Filename of path features stored as ArcGIS JSON
        conus_json_file: Filename of continental United States features stored
            as ArcGIS JSON. These features can be used as a basemap.
    """

    folder = path.dirname(gdb_path)
    gdb_name = path.basename(gdb_path)
    paths = gdb_path + '\\Paths'
    conus = gdb_path + '\\Conus'
    if not arcpy.Exists(gdb_path):
        arcpy.CreateFileGDB_management(folder, gdb_name, 'CURRENT')
    arcpy.JSONToFeatures_conversion(path_json_file, paths)
    if conus_json_file:
        arcpy.JSONToFeatures_conversion(conus_json_file, conus)
    print('Geodatabase {0} created at {1}'.format(gdb_name, gdb_path))

    mxd_filename = 'data/test.mxd'
    if path.exists(mxd_filename):
        mxd = arcpy.mapping.MapDocument(mxd_filename)
        for elm in arcpy.mapping.ListLayoutElements(mxd, 'TEXT_ELEMENT',
                                                    'splash'):
            elm.text = ' '
        mxd.save()
        del mxd
        print('Updated {}'.format(mxd_filename))


if __name__ == '__main__':
    root = path.dirname(__file__)
    arcpy.env.overwriteOutput = True
    gdb_path = path.join(root, 'data\\data.gdb')
    path_json_file = path.join(root, 'data\\paths.json')
    conus_json_file = path.join(root, 'data\\conus.json')
    create_gdb(gdb_path, path_json_file, conus_json_file)
