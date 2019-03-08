from frontend import *

def getCmds1():
	shape = UniformSolid(False)

	for n in range(5):
		scale = 1.0/(n+1)
		shape = Union(shape, Translate(Scale(Circle(), Vec2(scale,scale)), Vec2(0, n)))
	#shape2 = Scale(Square(), Vec2(0.2, 5))
	#field = SolidToField(shape2)
	#shape=ExpandSurface(shape, field, 0.2)

	return Output(shape)


def make_thing():
	thing = Circle()
	for i in range(0,360,45):
		leaf = Scale(Circle(), Vec2(0.5,0.5))
		leaf = Translate(leaf, Vec2(0,1))
		leaf = Rotate(leaf, i)
		thing = Union(thing, leaf)
	return Subtract(thing, Scale(Circle(),Vec2(0.5,0.5)))

def getCmds2():
	shape = UniformSolid(False)

	for n in range(5):
		scale = 1.0/(n+1)
		shape = Union(shape, Translate(Scale(make_thing(), Vec2(scale,scale)), Vec2(0, n)))

	selection = Translate(Scale(Square(), Vec2(2, 10)), Vec2(2, 0))
	selection = SolidToField(selection)
	blurred = BlurField(selection, 1)

	unused = BlurField(selection, 10)
	alsounused = Union(shape, Circle(), make_thing(), Square())

	final = ExpandSurface(shape, selection, 0.5)

	return Output(final)

def getCmds3():
	shape = Circle()
	shape2 = Translate(Circle(), Vec2(0.2, 0))
	shape3 = Subtract(shape, shape2)
	return Output(shape3)
