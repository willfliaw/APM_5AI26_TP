# Kernel Machines (APM_5AI26_TP) - 2024/2025

## Course Overview

This repository contains materials and resources for the course **APM_5AI26_TP: Kernel Machines**, part of the **Data Science** and **Data & Artificial Intelligence** curriculum. The course introduces kernel methods, a major tool in non-parametric machine learning, and covers their applications in regression, classification, dimensionality reduction, and structured output prediction.

### Key Topics:

1. Kernels and Reproducing Kernel Hilbert Space (RKHS) Theory: Understanding the theoretical foundation of kernel methods.
2. Kernel Machines: Applying kernels for regression, classification, and dimensionality reduction.
3. Kernel Design and Learning: Developing custom kernels and learning them from data.
4. Structured Output Prediction: Using kernel methods for multi-task learning and structured prediction.
5. Scaling Up Kernel Machines: Challenges and approaches to scaling kernel methods to large datasets.
6. Kernel Machines vs. Neural Networks: Exploring the relationship between kernel methods and neural networks.

The course is structured with 3 practical sessions to reinforce the theoretical concepts.

## Prerequisites

Students are expected to have:
- Basic knowledge of linear algebra, machine learning, and optimization.
- Familiarity with Python programming.

## Course Structure

- Total Hours: 24 hours of in-person sessions (16 sessions).
- Credits: 2 ECTS
- Evaluation: Final exam and lab reports.

## Instructor

- Professor Florence D'Alché

## Installation and Setup

Some exercises and projects require Python and relevant image processing libraries. You can follow the instructions below to set up your environment using `conda`:

1. Anaconda/Miniconda: Download and install Python with Anaconda or Miniconda from [Conda Official Site](https://docs.conda.io/en/latest/).
2. Image Processing Libraries: Create a new conda environment with the necessary packages:
   ```bash
   conda create -n nvark python pip numpy pandas scipy scikit-learn sktime cyl1tf ipykernel jupyter -c conda-forge
   ```
3. Activate the environment:
   ```bash
   conda activate kernel-machines
   ```
4. Launch Jupyter Notebook (if required for exercises):
   ```bash
   jupyter notebook
   ```

This setup will allow you to implement and test kernel methods for regression, classification, and dimensionality reduction.

## How to Contribute

Feel free to contribute to the repository by:
- Submitting pull requests for corrections or improvements.
- Providing additional examples or extending the projects.
