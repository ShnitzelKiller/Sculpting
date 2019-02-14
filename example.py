

"""
Core object types:

Solid: a 3d model with a definite boundary surface
Field: a "fuzzy" 3d model, probably represented as a 3d grid of float values 0 to 1 although not necessarily

Surface: a selection on the surface of a Solid. The selection itself has a definite decision boundary
SurfaceField: a "fuzzy" selection on the surface of a Solid
Both Surface types are only valid for the Solid they are created on.

To the user, all object types are immutable. Performing an operation will always return a new object.
I think the intermediate representation should be either hierarchical objects or discrete 3D SDF/voxel fields based on some internally decided criteria (hierarchical objects would get incomputable with some operations after a while)

The user will define a Solid as the final exported product. They can also define other object types as desired or use built in ones

Built in functions:

Returns a Solid:
	Empty(), Cube(), Sphere(), Cylinder() etc. Lets say all are centered at the origin and extend (-1,-1,-1) to (1,1,1)
	Translate(Solid, vector), Rotate(Solid, quaternion), Scale(Solid, vector) etc.
	Union(Solid, Solid), Intersect(Solid, Solid) etc.
	Sharpen(Field, float threshold): all areas in the field >= threshold are part of the resulting Solid

	MoveSurface(Solid, Field, vector): moves the solid's surface by vector - the area moved is defined by the field mask
	SmoothSurface(Solid, Field, radius): smoothes out sharp edges on the surface, radius is multiplied by the field at each point (does this work?)

Returns a Field:
	SolidToField(Solid): gives a field with 0-1 values only (maybe antialiased if we use a grid representation)
	Blur(Field, radius): 3d gaussian blur of a field (maybe mask with a second field?)
	Translate(Field, vector), Rotate Scale etc
	Add(Field, Field), Subtract(Field, Field), Min(Field, Field), Max(Field, Field) etc.

Example code:
"""

from frontend import *

def make_thing():
	thing = Circle()
	for i in range(0,360,45):
		leaf = Scale(Circle(), Vec2(0.5,0.5))
		leaf = Translate(leaf, Vec2(0,1))
		leaf = Rotate(leaf, i)
		thing = Union(thing, leaf)
	return Subtract(thing, Scale(Circle(),Vec2(0.5,0.5)))

shape = Empty()

for n in range(5):
	scale = 1.0/(n+1)
	shape = Union(shape, Translate(Scale(make_thing(), Vec2(scale,scale)), Vec2(0, n)))

selection = Translate(Scale(Square(), Vec2(2, 10)), Vec2(2, 0))
selection = SolidToField(selection)
blurred = BlurField(selection, 1)

unused = BlurField(selection, 10)

final = ExpandSurface(shape, selection, 0.5)

Output(final)