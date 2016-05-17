import inspect
import json
import os
import sys

import arcpy

sys.path.append('../arc_panimate')
import arc_panimate


def _demo_follow_line():
    """Demonstrate follow_line function.

    Requires data/demo.mxd next to this script. The map has a single dataframe
    with a line layer named Paths with an attribute named Path_Name.
    """

    outfolder = os.path.abspath('demo_follow_line')
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    mxd = arcpy.mapping.MapDocument('data/test.mxd')
    try:
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        lyr = arcpy.mapping.ListLayers(mxd, 'Paths', df)[0]
        with arcpy.da.SearchCursor(lyr, ['SHAPE@', 'Path_Name']) as cursor:
            for row in cursor:
                path_name = row[1]
                print 'Path: {}'.format(path_name)
                extents = arc_panimate.follow_line(
                    df, row[0], accelerate_steps=3, cruise_steps=3,
                    max_scale=10000000, target_scale=3000000)
                for i, ext in enumerate(extents):
                    print '    ', i
                    png_file = os.path.join(outfolder,
                                            path_name + '_{0:03d}'.format(i))
                    df.extent = ext
                    arcpy.mapping.ExportToPNG(mxd, png_file)
        raw_input('Images exported to:\n{}\n'
                  'Press Enter to continue.\n'.format(outfolder))
    except Exception as e:
        print e
    finally:
        del mxd


def _demo_save_extents():
    """Demonstrate save_extents function.

    Requires data/test.mxd next to this script.
    """

    outfolder = os.path.abspath('demo_save_extents')
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    outfile = os.path.join(outfolder, 'saved_extents.json')
    extents = []
    try:
        mxd = arcpy.mapping.MapDocument('data/test.mxd')
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        extents.append(df.extent)
        df.scale = df.scale * 1.5
        extents.append(df.extent)
        arc_panimate.save_extents(extents, outfile)
        raw_input('Extents saved to:\n{}\n'
                  'Press Enter to continue.\n'.format(outfile))
    except Exception as e:
        print e
    finally:
        del mxd


def _demo_load_extents():
    """Demonstrate load_extents function.

    Requires data/test.mxd and demo_save_extents/save_extents.json next to this
    script.
    """

    outfolder = os.path.abspath('demo_load_extents')
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    infile = 'demo_load_extents/saved_extents.json'
    extents = arc_panimate.load_extents(infile)
    try:
        mxd = arcpy.mapping.MapDocument('data/test.mxd')
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        for i, ext in enumerate(extents):
            df.extent = ext
            png_file = os.path.join(outfolder, 'extent_{0}'.format(i))
            arcpy.mapping.ExportToPNG(mxd, png_file)
        raw_input('Extents loaded and images exported to:\n{}\n'
                  'Press Enter to continue.\n'.format(outfolder))
    except Exception as e:
        print e
    finally:
        del mxd


if __name__ == '__main__':
    _demo_follow_line()
    _demo_save_extents()
    _demo_load_extents()
