

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

	ExtrudeSurface(Solid, Surface, vector): moves the surface according to vector, and creates new (straight, sharp edge) surface between old and new boundary
	MoveSurface(Solid, SurfaceField, vector): moves the surface by vector*field at each point, this is better for smoother extrusions
	SmoothSurface(Solid, SurfaceField, radius): smoothes out sharp edges on the surface, radius is multiplied by the field at each point

Returns a Field:
	FromSolid(Solid): gives a field with 0-1 values only (maybe antialiased if we use a grid representation)
	Blur(Field, radius): 3d gaussian blur of a field (maybe mask with a second field?)
	Add(Field, Field), Subtract(Field, Field), Min(Field, Field), Max(Field, Field) etc.

Returns a Surface:
	Select(Solid owner, Solid mask): returns a surface on owner containing areas within mask
	Union(Surface, Surface) etc.

Returns a SurfaceField:
	FromSurface(Surface): gives a surfaceField with 0-1 values only (maybe antialiased if we use a grid representation)
	Select(Solid owner, Field mask): returns a surface on owner with values based on mask
	Add(SurfaceField) etc.

Example code:
"""

def PineCone(Solid):
	outerarea = Sphere()
	mask = Blur(Translate(Sphere(), (0,1,0)), 1)
	surfmask = Select(outerarea, mask)
	outerarea = MoveSurface(outerarea, surfmask, (0,1,0)) #this makes kind of like a really smoothed cone with a round bottom

	spines = Empty()
	spine = scale(Cube(), (0.1, 1, 0.1))

	for n in range(1,50):
		nextspine = Translate(Rotate(spine, something), something) #basically making the spines stick out from the center sort of
		spines = Union(spines, nextspine)

	return Intersect(spines, outerarea)