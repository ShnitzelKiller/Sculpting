using PyCall

ex = pyimport("examples")

cmds = ex[:getCmds3]()

include("interpreter.jl")

result = execute(cmds)
