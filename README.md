# arc_panimate
Python module to support the creation of animations of images exported from ArcMap which follow the path defined by a line feature.

# Description

This Python 2.7 module is designed to support the creation of animations
consisting of image files exported from ArcMap which follow the path defined
by the geometry of a line feature. The module returns arcpy extent objects
representing the map extents to use when exporting images. The calling script
can then use the extents to export images or save the extents for later use.
The exported images can be assembled into a video file using video creation
software.

Demo video:
https://www.youtube.com/watch?v=67rJbNhZopA

# Requires

* ArcGIS for Desktop version 10.1 or greater.
* An ArcMap document from which images will be exported.
* A line feature class defining the paths to take during animation.

# Use Case

Suppose you want to create a video of Ebola outbreaks and containment over
time. The video should pan to a given hotspot, show a raster layer indicating
Ebola case density for each time step, and when the outbreak is contained the
map should pan to the next area with an outbreak.

Steps to build the video described in this use case:
 
1. Create line features representing the path the animation should take.
2. Author an ArcMap document with the page layout set up at the desired size
for images to be exported. Use the desired coordinate system. Keep layers with
a long drawing time out of the map for now. This makes extent generation 
quicker.
3. Write and run a script which feeds the line geometries to the follow_line 
function in arc_panimate.py and saves the resulting extents to a file.
4. Add all desired layers to the map and save it at the initial desired zoom
level.
5. Write and run a script which, for each desired time step, updates the
Ebola raster layer for the current time step and applies the associated 
extent as saved by arc_panimate.
6. Use movie editing software such as the free Windows Movie Maker to assemble
the exported images into a movie.

When you call `arc_panimate.follow_line` to generate extents, you pass the
number of steps (i.e., animation frames) to use. You can determine the number
of steps by considering the number of time steps you want to use panning along
the line. For example, for data with a daily time step, if there are 21 days
between Ebola outbreaks, you could spend 21 days (i.e., steps) panning along
the line from one outbreak to the next.

# Usage

To generate extents and export images at these extents:

```python
extents = arc_panimate.follow_line(
    dataframe, line_geometry, accelerate_steps=30, cruise_steps=30,
    max_scale=10000000, target_scale=3000000)
for i, ext in enumerate(extents):
    png_file = '{0:03d}'.format(i)
    dataframe.extent = ext
    arcpy.mapping.ExportToPNG(mxd, png_file)
```

arc_panimate includes a `save_extents` function for saving extents to a file
and a `load_extents` function for loading extents from a file.

# Tips

* The line feature should be digitized from the beginning point of the animation
to the end point. The feature should be in a feature class.
* For smoother animations, use curved line features. For help creating curved
line features, see the Curved Construction Tool in ArcGIS Online:
http://www.arcgis.com/home/item.html?id=2cc9375e467146dd8b8914c9c61429a1
* See the example folder for a script example and sample data.
