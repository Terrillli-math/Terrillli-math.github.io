# Editorial review for the website copy

These edits apply only to the Quarto site. The original Obsidian notes remain unchanged. The user should review the mathematical changes before publication.

| Website note | Substantive correction or caveat |
| --- | --- |
| Cantor's Theorem | Repaired the second branch of the diagonal contradiction and clarified that the theorem applies to infinite sets. |
| Functions Between Power Sets | Distinguished direct image from inverse image and stated when their compositions equal the identity. |
| Elementary Symmetric Polynomials | Corrected the general formula to use all $n$ variables, not just $k$. |
| Square Roots of Complex Numbers | Restricted the sign formula to $b\ne0$ and handled real numbers separately. |
| Basic Set Theory | Corrected membership examples: $6\notin\{1,2,3,4,5\}$ and $5\in\{1,4,5\}$. Marked the unfinished Replacement section as in progress. |
| Cardinality and Power Sets | Corrected the bijection from $\mathbb N$ to $\mathbb Z$; stated $|\mathbb R|=\aleph_1$ only under the continuum hypothesis; marked the final proof as in progress. |
| Cartesian Products | Replaced the misleading restriction to infinite sets with the general cardinal product statement. |
| Polynomials | Corrected the root-factor product from $n+1$ factors to $n$ and repaired malformed Vieta formatting. |
| Multiclass SVM | Clarified that class scores are not probabilities. Also clarified that the kernel trick avoids an explicit feature map; it does not automatically reduce computing cost. |

The shorter edits are English translation, grammar, and formatting. This log is kept so later changes to the source notes can be compared with the website version.

## MATH1972 Seminar Notes

The seminar pages rewrite the supplied handouts as connected study notes. The table separates mathematical corrections from explanations added for the website.

| Website Note | Mathematical Corrections or Caveats | Added Explanations |
| --- | --- | --- |
| Nim and Winning Moves | Makes the normal-play ending rule and player-to-move convention explicit. Supplies the missing justification behind the handout's compressed claim about combining positions. | Derives XOR from mex, proves the winning-move rule, and uses independently constructed practice positions, restricted-removal games, and a misère example. |
| Convex Sets and Functions | Requires affine equalities in the standard convex formulation. States the domain and smoothness assumptions for gradient and Hessian tests. Separates uniqueness from existence of a minimiser. | Adds segment arguments, a derivative-free local-to-global proof, and a ridge regression calculation that explains uniqueness. Keeps SDP and SILP at overview level. |
| Lagrange Duality and KKT Conditions | Uses an infimum for the dual function. Restores equality multipliers in KKT stationarity. Separates sufficient KKT conditions from necessity under a constraint qualification. Strong duality alone does not give primal attainment. | Proves weak duality and KKT sufficiency. Uses a constructed quadratic objective with two different bounds to compare inactive and active constraints. |
| Linear SVMs and Margins | Corrects the hard-margin primal from maximisation to minimisation where the SVM slides misprint it. Distinguishes score margin from distance, and hard-margin support vectors from soft-margin cases. Avoids claiming that a larger margin always improves generalisation. | Derives the distance and full margin width, the dual, the soft-margin multiplier bound, and the KKT cases. Adds a fully checked two-point example. |
| Feature Maps and Kernels | Explains that a feature map does not guarantee separation or lower computing cost. Requires an inner-product kernel rather than an arbitrary similarity score. | Checks a quadratic feature map by hand, proves that a Gram matrix is positive semidefinite, and separates the roles of C and the Gaussian width parameter. |
| Introduction to Network Analysis | Uses unordered edge pairs, zero diagonal entries, and edge counts in the sparsity discussion. Corrects adjacency powers to count walks. Repairs the distance formula and states disconnected-graph conventions. Separates global transitivity from average local clustering and states the low-degree convention. | Uses an independently constructed seven-node graph, new SVG diagrams, and newly calculated statistics. Includes the handshaking proof, local/global calculations, an isolated-node comparison, and a bridge-removal exercise. |

The worked numerical examples and graph structure were replaced with independently constructed examples. This includes new Nim positions and removal rules, shifted quadratic and KKT examples, a small ridge calculation, a two-point SVM, and feature-map calculations. Standard mathematical definitions and general proofs remain part of the exposition. The public references now list external sources only.

## Random Networks and Connectivity

### Mathematical Corrections and Caveats

- Finite degrees are binomial. The Poisson statement is a limit for each fixed nonnegative degree, including zero, when the edge probability vanishes and the mean degree tends to a positive constant.
- Independent edges do not give independent degrees or isolation indicators. The isolation-pair exponent is $2n-3$, because the shared absent edge must be counted only once. Both covariance terms are included in the calculations.
- For $p=c\log n/n$, the second-moment concentration proof applies to $0<c<1$, not to $c\leq1$. At $c=1$, the isolated-node expectation tends to one; the critical Poisson result is cited, not derived from expectation alone.
- Absence of isolated nodes is necessary but not sufficient for connectivity. The complete connectivity threshold is stated as a cited theorem, separate from the first-moment proof about isolated nodes.
- The logarithmic distance expression is a typical-distance heuristic inside the giant component for fixed mean degree greater than one. It is not an exact diameter formula. The whole sparse graph still has isolated nodes with high probability.
- Equal degree distributions do not force equal realised degrees. The model allows isolated nodes and degree outliers; its limitation is the homogeneous independent-edge assumption.

### Added Explanations and Examples

- Derives edge and degree laws from indicators, checks them with the handshaking lemma, and explains the difference between an expectation and an observed count.
- Supplies a short binomial-to-Poisson derivation, proofs of Markov and Chebyshev, and a folded isolation-variance derivation. Gives a counterexample showing why a diverging expectation alone is insufficient.
- Solves the finite-size equation for an expected single isolated node. Contrasts bounded mean degree with the larger connectivity scale, and links breadth-first layers to the short-route heuristic.
- Adds two reproducible $G(9,1/3)$ samples, a binomial/Poisson probability comparison, and exact expected-isolate curves. No source figures, simulation results, real-network data table, or teaching PDF is republished. Public references are external only.

## Exponential Random Graph Models

### Mathematical Corrections and Caveats

- The probability of a particular labelled graph has no binomial coefficient. The coefficient belongs to the probability of its edge count. Probabilities on this finite graph space are masses, not densities.
- Finite log-odds are real-valued for probabilities strictly between zero and one. Zero and one require infinite limiting logits. The edges-only MLE has the closed form $\widehat p=m/\binom n2$; a finite natural-parameter MLE exists only for an interior density in this case.
- Conditional edge independence given fixed node features is an assumption of the logistic special case, not a defining property of every ERGM. General triangle terms introduce edge dependence. General ERGM coefficients describe conditional odds through change statistics; conditional and marginal edge probabilities differ.
- The normalising constant depends on the model parameters and fixed covariates. It may cancel in a ratio between two graphs at the same parameter, but cannot be omitted from a likelihood as parameters vary.
- For an undirected node-covariate sum, a coefficient acts on $x_i+x_j$. It multiplies odds, not probabilities. This models activity rather than similarity. Positive associations do not force larger realised degrees or establish causal effects.
- A finite interior MLE matches the included statistics in expectation. Neither existence nor a unique identifiable fit is automatic. Standard errors and coefficient significance do not establish model fit. Distance checks must retain unreachable pairs, and a plug-in comparison is not automatically a calibrated hypothesis test.

### Added Explanations and Examples

- Builds the graph likelihood and derives the independent-edge MLE. Shows that all graphs of the same size have equal probability under $G(n,p)$, even when their shapes differ.
- Adds a new four-node graph with edges $12,13,23,34$, scores $(0,1,1,2)$, and a hand-checkable logistic example. The chosen slope and intercept are illustrative, not fabricated fitted coefficients or real measurements.
- Derives the logistic joint distribution, the identity $\sum_{i<j}a_{ij}(x_i+x_j)=\sum_i x_i d_i$, the ERGM normaliser, and the conditional edge formula by comparing graphs with and without one edge.
- Uses a new three-node edge-and-triangle model with coefficients $-\log2$ and $\log4$. All eight graphs give normaliser $15/4$, triangle probability $2/15$, expected edge count $6/5$, and marginal edge probability $2/5$. Conditional edge probabilities are $1/3$ or $2/3$.
- Explains likelihood equations as observed-minus-expected statistics. Keeps the derivative in a folded section; does not develop advanced estimation algorithms.
- Replaces the teaching material's data and diagnostic plots with new SVGs and an exact triangle-count check over all 64 labelled four-node graphs under $G(4,2/3)$. The observed graph has one triangle, and the model mean is $32/27$. Labels separate exact probabilities, observations, and illustrative parameter choices.
- Public references are external only. Original PDFs, QMD source, lecturer figures, R code, real-network data, and fitted result tables are not copied into the website. The Obsidian source remains unchanged. The three recurring source folders are unchanged.
