function partial!(B, A, dims...)
    R = CartesianIndices(A)
    Ifirst, Ilast = first(R), last(R)
    for (i, dim) in enumerate(dims)
        I1 = CartesianIndex([i == dim ? 1 : 0 for i=1:ndims(A)]...)
        for I in R
            B[i,I] = A[min(I+I1, Ilast)] - A[max(I-I1, Ifirst)]
        end
        for I in Ifirst+I1:Ilast-I1
            B[i,I] *= 0.5
        end
    end
    return B
end


function partial(A, dims...)
    B = Array{eltype(A)}(undef, length(dims), size(A)...)::Array{eltype(A), ndims(A) + 1}
    return partial!(B, A, dims...)
end
