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
| Nim and Winning Moves | Makes the normal-play ending rule and player-to-move convention explicit. Supplies the missing justification behind the handout's compressed claim about combining positions. | Derives XOR from mex, proves the winning-move rule, works through the four seminar exercises, and explains the two restricted-removal patterns and the misère caveat. |
| Convex Sets and Functions | Requires affine equalities in the standard convex formulation. States the domain and smoothness assumptions for gradient and Hessian tests. Separates uniqueness from existence of a minimiser. | Adds segment arguments, a derivative-free local-to-global proof, and a ridge regression calculation that explains uniqueness. Keeps SDP and SILP at overview level. |
| Lagrange Duality and KKT Conditions | Uses an infimum for the dual function. Restores equality multipliers in KKT stationarity. Separates sufficient KKT conditions from necessity under a constraint qualification. Strong duality alone does not give primal attainment. | Proves weak duality and KKT sufficiency. Contrasts the handout's inactive-constraint example with a simple active-constraint example. |
| Linear SVMs and Margins | Corrects the hard-margin primal from maximisation to minimisation where the SVM slides misprint it. Distinguishes score margin from distance, and hard-margin support vectors from soft-margin cases. Avoids claiming that a larger margin always improves generalisation. | Derives the distance and full margin width, the dual, the soft-margin multiplier bound, and the KKT cases. Adds a fully checked two-point example. |
| Feature Maps and Kernels | Explains that a feature map does not guarantee separation or lower computing cost. Requires an inner-product kernel rather than an arbitrary similarity score. | Checks a quadratic feature map by hand, proves that a Gram matrix is positive semidefinite, and separates the roles of C and the Gaussian width parameter. |
| Introduction to Network Analysis | Uses unordered edge pairs, zero diagonal entries, and edge counts in the sparsity discussion. Corrects adjacency powers to count walks. Repairs the distance formula and states disconnected-graph conventions. Separates global transitivity from average local clustering and states the low-degree convention. | Uses a checked six-node example instead of the missing data files and the inconsistent directed/undirected faculty-network counts. Adds original diagrams, the handshaking proof, local/global calculations, and an isolated-node comparison. |
