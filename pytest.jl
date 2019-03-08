using PyCall

py"""
from frontend import UniformSolid
def make_thing():
	thing = Circle()
	for i in range(0,360,45):
		leaf = Scale(Circle(), Vec2(0.5,0.5))
		leaf = Translate(leaf, Vec2(0,1))
		leaf = Rotate(leaf, i)
		thing = Union(thing, leaf)
	return Subtract(thing, Scale(Circle(),Vec2(0.5,0.5)))

for n in range(5):
	scale = 1.0/(n+1)
	shape = Translate(Scale(make_thing(), Vec2(scale,scale)), Vec2(0, n))

selection = Translate(Scale(Square(), Vec2(2, 10)), Vec2(2, 0))
selection = SolidToField(selection)
blurred = BlurField(selection, 1)

unused = BlurField(selection, 10)
alsounused = Union(shape, Circle(), make_thing(), Square())

final = ExpandSurface(shape, selection, 0.5)

command_list = Output(final)
"""

cmd_list = py"command_list"

include("interpreter.jl")

result = execute(cmd_list)
