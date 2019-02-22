using PyCall

ex = pyimport("example2")

cmds = ex[:getCmds]()

include("interpreter.jl")

result = execute(cmds)
