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

def average_vector(vectors, weights = None):
    if weights is None:
        weights = len(vectors)*[1]

    total_vector = len(vectors[0])*[0]
    total_weight = 0
    for k in range(len(vectors)):
        total_vector = add_vector(total_vector, scale_vector(vectors[k], weights[k]))
        total_weight += weights[k]

    return scale_vector(total_vector, 1/total_weight)

def scale_vector(v, scale):
    scales_vect = []
    for i in range(len(v)):
        scales_vect.append(v[i]*scale)
    return scales_vect

def heading(v):
    return math.atan2(v[1], v[0])

def bound_value(val, min_val, max_val):
    return (val if val > min_val else min_val) if val < max_val else max_val

def wrap_value(val, min_val, max_val):
    while val > max_val:
        val -= max_val - min_val
    while val < min_val:
        val += max_val - min_val
    return val

def wrap_angle(angle):
    return wrap_value(angle, -math.pi, math.pi)
