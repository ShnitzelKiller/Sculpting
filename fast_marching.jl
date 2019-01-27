using DataStructures

function compute_distance(grid::Matrix{T}, I, h, maxdist) where {T}
    Iv = CartesianIndex(1, 0)
    Ih = CartesianIndex(0, 1)
    R = CartesianIndices(grid)
    Ifirst, Ilast = first(R), last(R)

    Uh, Uv = [min([grid[J] for J in (min(I+Ii, Ilast), max(I-Ii, Ifirst)) if J != I]...) for Ii in (Ih, Iv)]

    if Uh < maxdist && Uv < maxdist
        disc = 2*h^2-(Uh-Uv)^2
        if disc >= 0
            return min(0.5*(Uh+Uv)+0.5*sqrt(disc), maxdist)
        end
    end

    Umin = min(Uv, Uh)
    return min(h+Umin, maxdist)
end
function fast_marching!(grid::Matrix{T}, h, maxdist=1) where {T}
    L = PriorityQueue{CartesianIndex{2}, T}()
    states = zeros(UInt8, size(grid)) #state 0: unvisited, 1: considered, 2: accepted
    for i in eachindex(grid)
        if grid[i] <= 0
            states[i] = 2
        else
            grid[i] = maxdist
        end
    end
    R = CartesianIndices(grid)
    Ifirst, Ilast = first(R), last(R)
    Iv = CartesianIndex(1, 0)
    Ih = CartesianIndex(0, 1)
    for I in R
        if states[I] == 0 &&
            (states[max(Ifirst, I-Iv)] == 2 ||
             states[max(Ifirst, I-Ih)] == 2 ||
             states[min(Ilast, I+Ih)] == 2 ||
             states[min(Ilast, I+Iv)] == 2)
            states[I] = 1
            dist = compute_distance(grid, I, h, maxdist)
            grid[I] = dist
            enqueue!(L, I, dist)
        end
    end
    #main loop
    while !isempty(L)
        I = dequeue!(L)
        states[I] = 2
        for Ii = (Iv, Ih)
            for J = (min(I+Ii, Ilast), max(I-Ii, Ifirst))
                if states[J] != 2
                    dist = compute_distance(grid, J, h, maxdist)
                    if dist < grid[J]
                        grid[J] = dist
                        if states[J] == 1
                            L[J] = dist
                        else
                            states[J] = 1
                            enqueue!(L, J, dist)
                        end
                    end
                end
            end
        end
    end
    return nothing
end
