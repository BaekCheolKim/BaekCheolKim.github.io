---
layout: minimal
title: Linear Algebra Terms
parent: Linear Algebra
grand_parent: Machine Learning
nav_order: 1
---

# Recap the terminology

## Key Concepts in Linear Algebra and Their Applications in Machine Learning

### 1. **Vector Space**
A vector space is one of many different spaces that is a collection of objects called vectors. The prime example is n-dimensional Euclidean space, which includes (x,y), (x,y,z), etc. <!--Function Spaces, Polynomial Spaces, and Sequence Spaces are other examples.--> We define vector spaces to provide a standardized framework, similar to Docker/Conda.

### 2. **Linear Independence**
Vectors are linearly independent if no vector can be written as a linear combination of the others. This property is essential in machine learning to ensure that datasets have sufficient variation for effective algorithm training.

### 3. **Orthogonality**
Two vectors are orthogonal if their dot product is zero. Orthogonality is a key concept in methods like Principal Component Analysis (PCA), where orthogonal vectors are used to capture the most variance in the data.

### 4. **Span**
The span of a set of vectors includes all points obtainable by linearly combining those vectors. In machine learning, understanding the span of vectors helps in comprehending the space occupied by the data points.

### 5. **Dimensionality**
Dimensionality refers to the number of entries in a vector or columns in a dataset. Reducing dimensionality without significant information loss is a common goal in machine learning, helping simplify models and reduce overfitting.

Dimensionality: In machine learning, dimensionality refers to the number of features or variables used to represent a single data point. It describes the inherent complexity of the data itself.
Multidimensional Arrays: These are data structures used in programming libraries like NumPy to store and manipulate data with multiple dimensions. The number of dimensions in a multidimensional array directly corresponds to the dimensionality of the data it represents.

### 6. **Rank**
The rank of a matrix indicates the maximum number of linearly independent column vectors it contains. It is crucial for understanding data structure in machine learning, such as identifying redundant features.

### 7. **Kernel and Range**
- **Kernel (Null Space):** The kernel of a matrix is the set of vectors mapped to zero by the matrix, representing solutions to the equation Ax = 0.
- **Range (Column Space):** The range of a matrix is the span of its columns, representing all possible outputs of the matrix transformation in machine learning.

### 8. **Determinant and Trace**
- **Determinant:** A scalar value that indicates whether a matrix is invertible and thus has full rank.
- **Trace:** The sum of the diagonal elements of a matrix, related to the eigenvalues and used in characterizing matrix operations.

### 9. **Matrix Decomposition**
Matrix decomposition involves breaking down a matrix into simpler matrices to facilitate operations such as solving linear equations and performing dimensionality reduction.

### 10. **Eigenvalues and Eigenvectors**
Eigenvalues and eigenvectors satisfy the equation Av = λv for a matrix A, where λ represents the eigenvalue, and v represents the eigenvector. These are vital in PCA and understanding system dynamics in machine learning.

### norm ###
Each concept builds on others, providing a comprehensive framework for understanding linear algebra's application in various fields, including machine learning, where they assist in data analysis, optimization, and model building.

