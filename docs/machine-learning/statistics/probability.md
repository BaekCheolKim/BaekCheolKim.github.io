---
layout: default
title: Probability
parent: Statistics
grand_parent: Machine Learning
nav_order: 2
---
Event Space, denoted ℱ, is the set of all
events.
• ℱ collection of all subsets of Ω including:
– Ω itself, meaning the sure event that “the
outcome is in Ω”
– The empty set ∅, meaning the impossible
event that “the outcome is not in Ω”

Dice Roll Example
• Random Experiment = Roll of Two Dice
• Sample Space Ω = { 𝑖, 𝑗 : 1 ≤ 𝑖, 𝑗 ≤ 6}
• Example Event = The sum of the two dice is 12, i.e. { 6,6 }
• Event Space ℱ =
{∅,Ω, 1,1 , 1,2 , 1,3 ,…, 6,6 ,…}

p(x) is the density of probability at 𝑥, indicating how likely it is to find 𝑋 near 𝑥. It is not the probability that 𝑋 equals 𝑥 because, for continuous variables, the probability of any specific value is zero. However, a higher 𝑝(𝑥) means 𝑋 is more likely to be found near 𝑥, implying a higher density of probability in that region.

# dependency : 
𝑋 and 𝑌 being independent means 𝑝(𝑥,𝑦)=𝑝(𝑥)𝑝(𝑦). However, even if 𝑋 and 𝑌 are independent, introducing a third variable 
𝑍 can create dependencies when conditioned on 𝑍. Thus, independence does not guarantee conditional independence given another variable 𝑍.

# Conditional Independency : 
𝑋 and 𝑌 are conditionally independent given 𝑍 if 𝑝(𝑥,𝑦∣𝑧)=𝑝(𝑥∣𝑧)𝑝(𝑦∣𝑧). This is a specific type of independence that holds when considering the influence of a third variable 𝑍.

# Examples
1. Conditional Independence Example:

Suppose 𝑋 is the score on a test, 𝑌 is the number of hours studied, and 
𝑍 is the difficulty level of the test. Given the difficulty level 
𝑍, the number of hours studied (𝑌) might not influence the score (𝑋) directly because the difficulty level accounts for the variations in the score.

2. Independence Example:

Suppose 𝑋 and 𝑌 are two dice rolls. They are independent since knowing the outcome of one roll does not affect the outcome of the other. If we condition on 𝑍 being the sum of the two rolls, 𝑋 and 𝑌 are no longer independent given 𝑍. For example, if 𝑍=12, knowing 𝑋=6 determines 𝑌 must be 6.

# difference between Conditional Independence and General Independence : 
conditional independence does not imply that 𝑋 and 𝑌 are independent without conditioning on 𝑍. And
General independence of 𝑋 and 𝑌 does not ensure that they will remain independent when conditioned on a third variable 𝑍.

# Variance :
Variance measures the spread or dispersion of a set of data points around their mean.  A higher variance indicates that the data points are more spread out from the mean, while a lower variance indicates that they are closer to the mean.
Var(X)=E[(X−μX)^2]

# Covariance :
Covariance measures the degree to which two random variables change together. It indicates the direction of the linear relationship between the variables.
1. A positive covariance means that when 𝑋 is above its mean, 𝑌 tends to be above its mean as well (and vice versa).
2. A negative covariance means that when 𝑋 is above its mean, 𝑌 tends to be below its mean (and vice versa).
3. A covariance of zero indicates no linear relationship between 𝑋 and 𝑌.
Cov(𝑋,𝑌)=𝐸[(𝑋−𝜇𝑋)(𝑌−𝜇𝑌)]

# Correlation :
Correlation quantifies the degree to which two variables are related, providing both the direction and the strength of the linear relationship. Unlike covariance, correlation is standardized and dimensionless.
−1 ≤ 𝜌 (𝑋, 𝑌) ≤ 1
ρ X,Y​ =Cov(X,Y)/σX​ σY
A correlation of 1 indicates a perfect positive linear relationship.
A correlation of -1 indicates a perfect negative linear relationship.
A correlation of 0 indicates no linear relationship.
The closer the value is to 1 or -1, the stronger the linear relationship.

interconnection : Variance is a special case of covariance when the two variables are the same (Var(𝑋)=Cov(𝑋,𝑋)).
Correlation standardizes covariance to make it easier to interpret the strength of the relationship between two variables.
 
# Gaussian Random Variables
 at a point 𝑥 ∈ 𝑅 as 𝑝(𝑥) = 𝑁 (𝑥; 𝜇, 𝜎^2) .

# Bayes’ Theorem
It is used to update the probability of a hypothesis based on new evidence. When you have an initial belief (prior probability) about an event and you receive new data or evidence, you can use Bayes' Theorem to update your belief (posterior probability).
For example, in medical diagnostics, if you know the prevalence of a disease (prior probability) and you get a test result (evidence), Bayes' Theorem helps you update the probability of having the disease (posterior probability).

p(x∣y)= p(y∣x)p(x) / p(y)

If 𝑋 is discrete, Bayes’ Theorem also
𝑝 (𝑥 |𝑦) = 𝑝 (𝑦| 𝑥) 𝑝 (𝑥)/Σx 𝑝(𝑥, 𝑦) = 𝑝 (𝑦| 𝑥) 𝑝 (𝑥) / Σx 𝑝 (𝑦| 𝑥) 𝑝(𝑥)

If 𝑋 is continuous, Bayes’ Theorem also
𝑝 (𝑥 |𝑦) = 𝑝 (𝑦| 𝑥) 𝑝 (𝑥)/∫ 𝑝(𝑥, 𝑦)𝑑𝑥 = 𝑝 (𝑦| 𝑥) 𝑝 (𝑥) / ∫ 𝑝 (𝑦| 𝑥) 𝑝(𝑥)𝑑𝑥