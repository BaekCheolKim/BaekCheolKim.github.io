---
layout: default
title: Robotics
nav_order: 8
has_children: true
permalink: /docs/robotics
---

# Robotics

# Pose and Kinematics
1.pose:Body-Fixed Frame (BFF)
Differential Drive Robot in 2D
𝜉=(𝑥,𝑦,𝜃)^T
how to express this?
Let c𝑒1 = (1,0)^T ,& c𝑒2 = (0,1)^T
v' = A_v_x * e'_1 + A_v_y * e'_2

Let the basis vectors of BFF expressed in BFF be B_e_1 and B_e_2

Let the basis vectors of BFF expressed in inertial frame be A_e_1 and A_e_2

BFF is  a coordinate system attached to the robot itself

2.pose velocity
it can be silplestly decomposed into linear velocity and angular velocity
3.kinetics

4. Body-Fixed Frame (BFF) vs. Reference Frame
Reference Frame: A frame with respect to which measurements are made.

BFF =  robot's velocity and orientation relative to itself
Reference Frame = where the robot is in the world.

# Some Philosophy Behind Pose

Describing or Measuring the pose of an object requires reference to the surrounding world. This is captured by the concept of a physical observer -- that is an entity that observes the object.