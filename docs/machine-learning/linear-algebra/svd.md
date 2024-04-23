---
layout: default
title: SVD
parent: Machine Learning
nav_order: 1
---

# Singular Value Decomposition (SVD)

## Introduction
Singular Value Decomposition (SVD) is a mathematical technique used in linear algebra that factors a matrix into three distinct matrices. These components reveal important properties of the original matrix and are used in a wide range of applications from signal processing to machine learning.

## Mathematical Background
The SVD of a matrix \( A \) that is \( m \times n \) decomposes \( A \) into three matrices \( U \), \( \Sigma \), and \( V^T \) such that:

\[ A = U \Sigma V^T \]

- \( U \) is an \( m \times m \) orthogonal matrix.
- \( \Sigma \) is an \( m \times n \) diagonal matrix with non-negative real numbers on the diagonal.
- \( V^T \) is an \( n \times n \) orthogonal matrix where \( T \) denotes the transpose of \( V \).

The columns of \( U \) and \( V \) are called the left-singular vectors and right-singular vectors of \( A \), respectively. The diagonal values of \( \Sigma \) are known as the singular values of \( A \).

## Applications
SVD is incredibly versatile and finds applications in:

- **Dimensionality Reduction**: In fields like image processing and text mining.
- **Noise Reduction**: Used in signal processing.
- **Data Compression**: Helpful in reducing storage and improving speed without losing too much information.
- **Recommendation Systems**: Used to predict people's item preferences.

## Example
Consider a matrix \( A \) of size \( 3 \times 4 \). The SVD of \( A \) can be calculated using various programming tools like Python's NumPy library:

```python
import numpy as np

A = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
U, s, VT = np.linalg.svd(A, full_matrices=False)
print("U matrix:\n", U)
print("Singular values:", s)
print("V^T matrix:\n", VT)

