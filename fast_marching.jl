using DataStructures

function compute_distance(grid::Matrix{T}, I::CartesianIndex{2}, Ifirst::CartesianIndex{2}, Ilast::CartesianIndex{2}, h::Real, maxdist::Real) where {T <: AbstractFloat}
    Iv = CartesianIndex(1, 0)
    Ih = CartesianIndex(0, 1)

    Uh = Uv = maxdist
    function m(Ii)
        Jfirst = max(I-Ii, Ifirst)
        Ufirst = Jfirst == I ? maxdist : grid[Jfirst]
        Jlast = min(I+Ii, Ilast)
        Ulast = Jlast == I ? maxdist : grid[Jlast]
        Umin = min(Ufirst, Ulast)
    end
    Uh, Uv = m(Ih), m(Iv)

    if Uh < maxdist && Uv < maxdist
        disc = 2*h^2-(Uh-Uv)^2
        if disc >= 0
            return min(0.5*(Uh+Uv)+0.5*sqrt(disc), maxdist)
        end
    end

    Umin = min(Uv, Uh)
    return min(h+Umin, maxdist)
end
function fast_marching!(states::Matrix{UInt8}, grid::Matrix{T}, h::Real, maxdist::Real) where {T <: AbstractFloat}
    L = PriorityQueue{CartesianIndex{2}, T}()
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
            dist = compute_distance(grid, I, Ifirst, Ilast, h, maxdist)
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
                    dist = compute_distance(grid, J, Ifirst, Ilast, h, maxdist)
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
function fast_marching!(grid::Matrix{T}, h::Real, maxdist::Real=1) where {T <: AbstractFloat}
    states = zeros(UInt8, size(grid))::Matrix{UInt8}
    fast_marching!(states, grid, h, maxdist)
end
