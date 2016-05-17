#!/usr/bin/python2
"""Determines map extents from ArcMap following line geometry.

Requires:
    arcpy for ArcGIS version 10.1 or greater
"""

import json
import os

import arcpy


def _project_to_df_spatial_ref(input_geometry, df_spatial_ref):
    """Project input arcpy geometry to match input arcpy spatial reference."""
    
    error_message = ('Warning: {} spatial reference is unknown. Cannot project'
                     'path geometry to match map.')
    in_spatial_ref = input_geometry.spatialReference
    if df_spatial_ref.name == 'Unknown':
        print error_message.format('Dataframe')
    elif in_spatial_ref.name == 'Unknown':
        print error_message.format('Path geometry')

    # This arcpy geometry function projects when spatial references are known,
    # and returns a copy of the input_geometry if either spatial reference is
    # unknown
    return input_geometry.projectAs(df_spatial_ref)


def save_extents(extent_list, filename):
    """Serialize a list of arcpy extent objects to a JSON file."""

    data = [json.loads(e.JSON) for e in extent_list]
    with open(filename, 'wb') as f:
        f.write(json.dumps(data))


def load_extents(extent_json):
    """Deserialize a list of arcpy extent objects from a JSON file.

    The JSON structure is:
    [{
            "xmin": -409983.0937753967,
            "ymin": -172289.08177567608,
            "ymax": 31086.537479010625,
            "xmax": -138815.60143581446,
            "spatialReference": {
                    "wkid": 102005,
                    "latestWkid": 102005
            }
    }, ...]
    """

    with open(extent_json) as f:
        data = json.load(f)
    extents = [arcpy.Extent(d['xmin'], d['ymin'], d['xmax'], d['ymax'])
               for d in data]
    return extents


def _get_line_positions(accelerate_steps, cruise_steps):
    """Determine positions from zero to one given number of steps to take."""
    
    if accelerate_steps == 0 and cruise_steps == 0:
        pcts = [0]
    elif accelerate_steps == 0:
        pcts = [float(i) / cruise_steps for i in range(cruise_steps + 1)]
    elif accelerate_steps > 0 and cruise_steps > 0:
        accel_rate = 1.0 / (accelerate_steps * cruise_steps +
                            accelerate_steps**2)
        accel_pcts = [0.5 * accel_rate * i**2
                      for i in range(accelerate_steps + 1)]
        cruise_vel = accel_rate * accelerate_steps
        cruise_start_pct = accel_pcts[-1] + cruise_vel
        cruise_pcts = [cruise_start_pct + cruise_vel * i
                       for i in range(cruise_steps)]
        decel_pcts = [1.0 - accel_pcts[i] for i in range(accelerate_steps)]
        decel_pcts.reverse()
        pcts = accel_pcts + cruise_pcts + decel_pcts
    else:  # accelerate_steps > 0 and cruise_steps == 0
        accel_rate = 1.0 / accelerate_steps**2
        accel_pcts = [0.5 * accel_rate * i**2
                      for i in range(accelerate_steps + 1)]
        decel_pcts = [1.0 - accel_pcts[i] for i in range(accelerate_steps)]
        decel_pcts.reverse()
        pcts = accel_pcts + decel_pcts
    return pcts


def _get_scales(accelerate_steps, cruise_steps,
                start_scale, max_scale, target_scale):
    """Determine scale to use at each step given input steps."""
    
    if accelerate_steps == 0 and cruise_steps == 0:
        scales = [target_scale]
    elif accelerate_steps == 0:
        rising_steps = cruise_steps / 2
        falling_steps = rising_steps + cruise_steps % 2
        rising = [start_scale]
        if rising_steps:
            scale_step = (max_scale - start_scale) / float(rising_steps)
            rising_scales = [start_scale + scale_step * (i + 1)
                             for i in range(rising_steps)]
            rising.extend(rising_scales)
        scale_step = (max_scale - target_scale) / float(falling_steps)
        falling = [target_scale + scale_step * i
                   for i in range(falling_steps)]
        falling.reverse()
        scales = rising + falling

    else:
        middle = [max_scale] * cruise_steps

        if accelerate_steps > 3:
            scale_accel_steps = accelerate_steps / 2
            scale_decel_steps = scale_accel_steps + accelerate_steps % 2
            scale_rate = (
                (max_scale - start_scale) /
                (0.5 * (scale_accel_steps**2 - scale_decel_steps**2) +
                 scale_accel_steps * scale_decel_steps))
            rising = [start_scale + 0.5 * scale_rate * i**2
                      for i in range(scale_accel_steps + 1)]
            decel_scales = [max_scale - 0.5 * scale_rate * i**2
                            for i in range(scale_decel_steps)]
            decel_scales.reverse()
            rising.extend(decel_scales)

            scale_rate = (
                (max_scale - target_scale) /
                (0.5 * (scale_accel_steps**2 - scale_decel_steps**2) +
                 scale_accel_steps * scale_decel_steps))
            falling = [max_scale - 0.5 * scale_rate * (i + 1)**2
                       for i in range(scale_accel_steps)]
            decel_scales = [target_scale + 0.5 * scale_rate * i**2
                            for i in range(scale_decel_steps)]
            decel_scales.reverse()
            falling.extend(decel_scales)
        else:
            # Not enough steps for acceleration and deceleration, so go linear
            scale_step = (max_scale - start_scale) / float(accelerate_steps)
            rising = [start_scale + scale_step * i
                      for i in range(1 + accelerate_steps)]
            scale_step = (target_scale - max_scale) / float(accelerate_steps)
            falling = [max_scale + scale_step * (i + 1)
                       for i in range(accelerate_steps)]
        scales = rising + middle + falling
    return scales


def follow_line(dataframe, line_geometry, accelerate_steps=0, cruise_steps=0,
                max_scale=None, target_scale=None):
    """Return map extents panning to follow the shape of a line geometry.

    This function is intended to support animation by defining a series of map
    extents to use when exporting maps. The input line geometry defines the
    path the frames will take. You should author this geometry in ArcMap prior
    to running this script, or generate the geometry with code.

    Regardless of number of pan steps provided, an extent is included at the
    beginning of the line to represent the starting point of the pan. Thus, the
    total number of extents is 1 + cruise_steps + 2 * accelerate_steps.

    We use the acceleration formula: distance = 0.5 * acceleration * time**2

    A maximum scale at the end of acceleration can be provided, as can a target
    scale for the end of the animation. If no acceleration is provided, max
    scale is achieved halfway through cruise. If acceleration and cruise are
    not provided, max_scale is ignored and target_scale is used. The starting
    scale is the original scale in the map. 

    We step linearly for scaling for less than 4 acceleration steps. Otherwise,
    we accelerate and decelerate scale adjustments during motion acceleration
    and deceleration.

    Args:
        dataframe: ArcMap dataframe object representing the map to export.
        line_geometry: arcpy geometry object of the line to follow.
        accelerate_steps: Integer number of steps to accelerate the pan at the
            beginning of the line and decelerate the pan at the end. This makes
            the motion appear smoother.
        cruise_steps: Integer number of steps to cruise during pan. Cruising
            occurs between acceleration and deceleration steps if provided or
            throughout the entire pan if acceleration is not provided. Cruising
            occurs at maximum scale if provided. 
        max_scale: (Double) Maximum map scale to zoom out to during the pan.
            If provided, the map cruises at the max scale. If no cruise steps
            are provided, the map reaches max scale at the end of acceleration
            steps.
        target_scale: (Double) Target map scale for the end of the pan. If not
            provided, original map scale is used.

    Returns: List of extent objects representing each frame along the pan.
    """

    extents = []
    geom = _project_to_df_spatial_ref(
        line_geometry, dataframe.spatialReference)

    start_scale = dataframe.scale
    if not target_scale:
        target_scale = start_scale
    if not max_scale:
        max_scale = (target_scale + start_scale) / 2.0

    percents_along_line = _get_line_positions(accelerate_steps, cruise_steps)
    scales = _get_scales(
        accelerate_steps, cruise_steps, start_scale, max_scale, target_scale)

    # Pan and zoom to each percentage along the line
    for i, percent in enumerate(percents_along_line):
        extent = geom.positionAlongLine(percent, True).extent
        dataframe.scale = scales[i]
        dataframe.panToExtent(extent)
        extents.append(dataframe.extent)

    return extents
