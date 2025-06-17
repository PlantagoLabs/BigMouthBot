import math

def norm(a):
    return math.sqrt(norm_sq(a))

def norm_sq(a):
    return dot(a, a)

def dot(a, b):
    total = 0.0
    for i in range(len(a)):
        total += a[i]*b[i]
    return total

def cosine_sq(a, b):
    dot_a_b = dot(a, b)
    return (dot_a_b*dot_a_b)/(norm_sq(a)*norm_sq(b))

def cosine(a, b):
    return dot(a, b)/(norm(a)*norm(b))

def add_vector(a, b):
    add_vect = []
    for i in range(len(a)):
        add_vect.append(a[i] + b[i])
    return add_vect

def diff_vector(a, b):
    diff_vect = []
    for i in range(len(a)):
        diff_vect.append(a[i] - b[i])
    return diff_vect

def scale_vector(v, scale):
    scales_vect = []
    for i in range(len(v)):
        scales_vect.append(v[i]*scale)
    return scales_vect