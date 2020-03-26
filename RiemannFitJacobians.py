from sympy import Symbol, symbols
from sympy import simplify
from sympy import sin, cos, atan
from sympy.matrices import Matrix
from sympy import pprint
from sympy import factor,expand,diff
from sympy import sqrt
from sympy import latex
from sympy.vector import CoordSys3D


a,b,x,y,r,t,Vrr,Vrt,Vtt = symbols('a,b,x,y,r,t,V_rr,V_rt,V_tt', real=True)
s11,s12,s13,s14,s15,s21,s22,s23,s24,s25,s31,s32,s33,s34,s35,s41,s4,s43,s44,s45,s51,s52,s53,s54,s55 = symbols('s1:6(1:6)', real=True)
Vxx, Vxy, Vxz, Vyx, Vyy, Vyz, Vzx, Vzy, Vzz = symbols('V_x:z(x:z)', real=True)
x11, x12, x21, x22 = symbols('x_1:3(1:3)')
y11, y12, y21, y22 = symbols('y_1:3(1:3)')
(x1, x2) = symbols('x_1:3')
(y1, y2) = symbols('y_1:3')
(Vr1r1, Vr1r2, Vr2r1, Vr2r2) = symbols('V_r1:3(1:3)')
(Vt1t1, Vt1t2, Vt2t1, Vt2t2) = symbols('V_t1:3(1:3)')
(Vr1t1, Vr1t2, Vr2t1, Vr2t2) = symbols('V_r1:3t1:3')
(Vt1r1, Vt1r2, Vt2r1, Vt2r2) = symbols('V_t1:3r1:3')
(r1,r2) = symbols('r_1:3')

PRINT_LATEX = 1

def printCentral(expression):
  if PRINT_LATEX:
    pprint(latex(expression, mode='equation', mat_str='smallmatrix'))
  else:
    pprint(expression)


if PRINT_LATEX:
    print("\\documentclass[8pt]{article}")
    print("\\usepackage{amsmath}")
    print("\\usepackage[landscape]{geometry}")
    print("\\begin{document}")

# Let's study the simple case u = a*x + b*y, with Cov(x,y)
# Jacobian = [df/dx, df/dy] = [a, b]
# Hence the Cov(u) = J * Cov(x,y) * JT

J = Matrix([[diff(a*x+b*y, x), diff(a*x+b*y, y)]])
Cov_xy = Matrix([[Vxx, Vxy], [Vxy, Vyy]])
print("\nFor the case u = a*x + b*y we have a Cov(u):")
printCentral(expand(J * Cov_xy * J.T))





# Case of cartesian to polar transformation
# x = r cos(t) = f1
# y = r sin(t) = f2
# Rotation matrix R = [[cos(t), -sin(t)], [sin(t), cos(t)]]

V_xy = Matrix([[Vxx, Vxy], [Vxy, Vyy]])
J = Matrix([[cos(t), -sin(t)], [sin(t), cos(t)]])

print("\nFor the case of going from x,y to r,theta(t), using a Rotation")
printCentral(V_xy)

print("\nRotation Matrix:")
printCentral(J)

print("\nFinal(destination) covariance Matrix:")
printCentral(expand(J * V_xy * J.T))





# Case of cartesian to polar transformation
# x = r cos(t) = f1
# y = r sin(t) = f2
# Jacobian = [[df1/dr, df1/dt], [df2/dr, df2/dt]] = [[cos(t), -r*sin(t)], [sin(t), r*cos(t)]]

print("\n\n\nCase of cartesian to polar transformation")
Var_xy = Matrix([[Vxx, Vxy], [Vxy, Vyy]])
print("\nCartesian Variance:")
printCentral(Var_xy)

Jacobian_cart_to_polar = Matrix([[diff(r*cos(t),r) , diff(r*cos(t), t)], [diff(r*sin(t), r), diff(r*sin(t), t)]])
print("\nJacobian-cart-to-polar:")
printCentral(Jacobian_cart_to_polar)

print("\nPolar Variance:")
printCentral(expand(Jacobian_cart_to_polar * Var_xy * Jacobian_cart_to_polar))


# Case of polar coordinates to cartesian transtormation
# r = sqrt(x^2+y^2) = f1
# t = atan(y/x) = f2
# Jacobian = [[df1/dx, df1/dy], [df2/dx, df2/dy]] = [[x/r, y/r], [-y/r^2, x/r^2]]

print("\n\n\nCase of polar to cartesian transformation")
Var_rt = Matrix([[Vrr, Vrt], [Vrt, Vtt]])
print("\nPolar Variance:")
printCentral(Var_rt)

f1 = sqrt(x**2+y**2)
f2 = atan(y/x)
Jacobian_rad_to_cart = Matrix([[f1.diff(x).subs(x**2+y**2,r**2), f1.diff(y).subs(x**2+y**2,r**2)],
                               [factor(f2.diff(x)).subs(x**2+y**2,r**2), factor(f2.diff(y)).subs(x**2+y**2,r**2)]])
print("\nJacobian-rad-to-cart:")
printCentral(Jacobian_rad_to_cart)

print("\nCartesian Variance:")
printCentral(expand(Jacobian_rad_to_cart * Var_rt * Jacobian_rad_to_cart.T))





# Case of polar to cartesian coordinates, with several points using a block matrix.
# Input Cov is: [[Vr1r1, Vr1r2, Vr1t1, Vr1t2],
#                [Vr1r2, Vr2r2, Vr2t1, Vr2t2],
#                [Vt1r1, Vt1r2, Vt1t1, Vt1t2],
#                [Vt2r1, Vt2r2, Vt2t1, Vt2t2]]
#
# Also the Jacobian becomes block-ed
#
# Jacobian_block = [[x1/r1, 0, y1/r1, 0],
#                   [0, x2/r2, 0, y2/r2],
#                   [-y1/r1**2, 0, x1/r1**2, 0],
#                   [0, -y2/r2**2, 0, x2/r2**2]]

print("\n\n\nPolar to Cartesian transformation, using multiple points with block matrices.")

print("\nInput Covariance block matrix:")
Var_block = Matrix([[Vr1r1, Vr1r2, Vr1t1, Vr1t2],
                    [Vr1r2, Vr2r2, Vr2t1, Vr2t2],
                    [Vt1r1, Vt1r2, Vt1t1, Vt1t2],
                    [Vt2r1, Vt2r2, Vt1t2, Vt2t2]])
printCentral(Var_block)

print("\nJacobian block matrix:")
Jacobian_block = Matrix([[x1/r1, 0, y1/r1, 0],
                         [0, x2/r2, 0, y2/r2],
                         [-y1/r1**2, 0, x1/r1**2, 0],
                         [0, -y2/r2**2, 0, x2/r2**2]])
printCentral(Jacobian_block)

print("\nCartesian Covariance block matrix:")
printCentral(expand(Jacobian_block * Var_block * Jacobian_block.T))



# Now we compute the Jacobian for the s variable for the  line fit.

x0,y0,xi,yi,q,R = symbols('X_0, Y_0 x_i, y_i q R')
N = CoordSys3D('N')
o = x0*N.i + y0*N.j
tmp = xi*N.i + yi*N.j
a = -o
b = tmp - o

print("\n\n\nInput values:")
print("\na:")
printCentral(a)
print("\nb:")
printCentral(b)

c_ = expand((a ^ b) & N.k)
d_ = expand(a & b)
c2_d2 = factor(c_**2+d_**2)
k = -q*R/c2_d2

print("\ncross:")
printCentral(c_)

print("\ndot:")
printCentral(d_)

c2_d2 = factor(c_**2+d_**2)

km = k*(x0**2+y0**2)
print("\nkm:")
printCentral(km)

print("\nk:")
printCentral(k)
print("\nk also as:")
printCentral(k.subs(c2_d2, 'dot**2+cross**2'))
print("\ni.e. k:")
printCentral(k.subs(km,'km'))

s = -q * R * atan(c_/d_)
print("\ns:")
printCentral(s.subs(d_,'dot').subs(c_,'cross'))

# compute the Jacobian

Jacobian_s = Matrix([
    factor(diff(s,x0)).subs(k, 'k'),
    factor(diff(s,y0)).subs(k, 'k'),
    simplify(factor(diff(s,R))).subs(d_,'dot').subs(c_,'cross'),
    factor(diff(s,xi)).subs(km, 'km'),
    factor(diff(s,yi)).subs(-km, '-km')
    ])


print("\nJacobian [x0, y0, R, xi, yi]:")
printCentral(Jacobian_s)

print("\nNote that -(b_y - a_y)*dot + (b_x + a_x)*cross is:")
printCentral(factor(-(b.components[N.j] - a.components[N.j])*d_ + (b.components[N.i] + a.components[N.i])*c_))

print("\nNote that (b_x - a_x)*dot - (-a_y - b_y)*cross is:")
printCentral(factor((b.components[N.i] - a.components[N.i])*d_ - (-a.components[N.j] - b.components[N.j])*c_))

print("\nNote that -a_y*dot - a_x*cross is:")
printCentral(factor(-a.components[N.j]*d_ - a.components[N.i]*c_))

print("\nNote that a_x*dot-a_y*cross is:")
printCentral(factor(a.components[N.i]*d_ - a.components[N.j]*c_))


if PRINT_LATEX:
    print("\\end{document}")
