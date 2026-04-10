# kevinychen/nikoli-puzzle-solver (Star Battle) - Algorithm & Architecture Analysis

> Analysis of [kevinychen/nikoli-puzzle-solver](https://github.com/kevinychen/nikoli-puzzle-solver) — specifically [`src/solvers/starbattle.ts`](https://github.com/kevinychen/nikoli-puzzle-solver/blob/main/src/solvers/starbattle.ts)

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Solving Approach: Declarative Constraint Solving via Z3](#solving-approach-declarative-constraint-solving-via-z3)
- [The Star Battle Solver — Line-by-Line Breakdown](#the-star-battle-solver--line-by-line-breakdown)
- [Constraint Model](#constraint-model)
- [Framework Architecture](#framework-architecture)
- [Hex Grid Support](#hex-grid-support)
- [Comparison with Other Analyzed Solvers](#comparison-with-other-analyzed-solvers)
- [Applicability to Our Goals](#applicability-to-our-goals)

---

## Project Overview

This is a **web-based solver for 100+ Nikoli-style logic puzzles** (Sudoku, Slitherlink, Masyu, Star Battle, etc.) built on top of the **Z3 SMT solver**. The Star Battle solver is one of many puzzle solvers in the framework, and it demonstrates a fundamentally different paradigm from the backtracking (hartez) and deduction-based (gjohnhazel) approaches previously analyzed.

The key insight of this project: **every Nikoli puzzle can be expressed as a set of mathematical constraints and solved by an off-the-shelf SMT solver**. The Star Battle solver is just ~30 lines of TypeScript — it declares the rules, and Z3 does all the work.

The project is **solver-only** — it has no puzzle generator, no hint system, and no difficulty grading. It integrates with the Penpa UI for puzzle input/output.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | TypeScript (93.3% of codebase) |
| Build | Webpack, Node.js 20.6.1+ |
| Constraint Solver | **Z3** (Microsoft's SMT solver, via z3-solver npm package) |
| Puzzle UI | Penpa (external puzzle editor) |
| Framework Inspiration | Grilops (Python puzzle solver library) |

### What is Z3?

Z3 is an **SMT (Satisfiability Modulo Theories) solver** developed by Microsoft Research. It takes a set of logical/mathematical constraints and either finds a satisfying assignment or proves none exists. For puzzle solving, this means:

1. Declare variables (one per cell)
2. Declare constraints (the puzzle rules)
3. Call `solve()` — Z3 handles all search, backtracking, and propagation internally
4. Read the model (the solution)

Z3 uses highly optimized algorithms internally — DPLL(T), conflict-driven clause learning (CDCL), theory propagation, and more. These are far more sophisticated than hand-written backtracking solvers.

---

## Solving Approach: Declarative Constraint Solving via Z3

This solver represents a **declarative** paradigm — the programmer describes *what* the solution looks like, not *how* to find it. Compare:

| Paradigm | Example | Who does the search? |
|----------|---------|---------------------|
| **Imperative backtracking** | hartez/starBattle (Go) | Programmer writes the search loop, branching, and pruning |
| **Deduction-based** | gjohnhazel/StarBattleSolver | Programmer writes pattern-matching strategies |
| **Declarative constraint** | nikoli-puzzle-solver (Z3) | Programmer declares constraints; Z3 searches internally |

The declarative approach trades control for brevity and correctness. The programmer can't tune the search heuristics, but they also can't introduce search bugs.

---

## The Star Battle Solver — Line-by-Line Breakdown

The complete solver is remarkably concise:

```typescript
import { Constraints, Context, Puzzle, Solution, Symbol, ValueMap } from "../lib";

const solve = async ({ Or, Sum }: Context, puzzle: Puzzle, cs: Constraints, solution: Solution) => {
    // 1. Create a 0/1 integer variable for each cell
    const grid = new ValueMap(puzzle.points, _ => cs.int(0, 1));

    // 2. Adjacency constraint: no two stars may touch (king's move)
    for (const [p] of grid) {
        for (const q of puzzle.points.vertexSharingPoints(p)) {
            cs.add(Or(grid.get(p).eq(0), grid.get(q).eq(0)));
        }
    }

    // 3. Row and column constraints: exactly N stars per line
    const numStars = parseInt(puzzle.parameters["stars"]);
    for (const [line] of puzzle.points.lines()) {
        cs.add(Sum(...line.map(p => grid.get(p))).eq(numStars));
    }

    // 4. Region constraints: exactly N stars per region
    for (const region of puzzle.regions()) {
        cs.add(Sum(...region.map(p => grid.get(p))).eq(numStars));
    }

    // 5. Solve and extract the model
    const model = await cs.solve(grid);

    // 6. Mark solved cells
    for (const [p, arith] of grid) {
        if (model.get(arith)) {
            solution.symbols.set(p, Symbol.STAR);
        }
    }
};
```

That's the entire solver. ~30 lines of meaningful code.

---

## Constraint Model

The solver encodes Star Battle as a **pseudo-Boolean constraint satisfaction problem**:

### Variables

For an NxN grid, create N*N integer variables, each bounded to {0, 1}:
- `grid[p] = 0` means no star at point p
- `grid[p] = 1` means star at point p

```typescript
const grid = new ValueMap(puzzle.points, _ => cs.int(0, 1));
```

The `cs.int(0, 1)` call creates a Z3 integer constant with bounds `0 <= x <= 1`, effectively a Boolean variable represented as an integer (needed for the Sum constraints).

### Constraint 1: No Adjacent Stars (King's Move)

For every pair of cells (p, q) that share a vertex (horizontally, vertically, or diagonally adjacent):

```
grid[p] = 0  OR  grid[q] = 0
```

This means at most one of any two adjacent cells can contain a star.

```typescript
for (const [p] of grid) {
    for (const q of puzzle.points.vertexSharingPoints(p)) {
        cs.add(Or(grid.get(p).eq(0), grid.get(q).eq(0)));
    }
}
```

**Note**: This generates redundant constraints — if p and q are adjacent, both `Or(p=0, q=0)` and `Or(q=0, p=0)` are generated. Z3 handles redundancy efficiently, so this doesn't affect correctness, only adds minor overhead during constraint setup.

An alternative formulation would be `grid[p] + grid[q] <= 1`, which avoids the Or and uses arithmetic instead.

### Constraint 2: Star Count per Row and Column

For each row and each column, the sum of all variables in that line equals the required star count:

```
Sum(grid[p] for p in row_i) = numStars    for each row i
Sum(grid[p] for p in col_j) = numStars    for each column j
```

```typescript
for (const [line] of puzzle.points.lines()) {
    cs.add(Sum(...line.map(p => grid.get(p))).eq(numStars));
}
```

The `puzzle.points.lines()` method yields both rows and columns (and potentially other line types for non-rectangular grids).

### Constraint 3: Star Count per Region

For each region, the sum of all variables in that region equals the required star count:

```
Sum(grid[p] for p in region_r) = numStars    for each region r
```

```typescript
for (const region of puzzle.regions()) {
    cs.add(Sum(...region.map(p => grid.get(p))).eq(numStars));
}
```

### Total Constraint Count

For a standard 10x10/2-star puzzle:
- **Adjacency constraints**: Up to 10*10*8 = 800, but boundary cells have fewer neighbors. In practice ~360 unique adjacency pairs (720 generated due to symmetry).
- **Line constraints**: 10 rows + 10 columns = 20
- **Region constraints**: 10 regions = 10
- **Total**: ~750 constraints, 100 variables

This is a trivially small problem for Z3, which routinely handles millions of constraints.

---

## Framework Architecture

### Registry Pattern

Each puzzle solver registers itself with a global registry:

```typescript
solverRegistry.push({
    name: "Star Battle",
    parameters: "stars: 2",
    solve,
    samples: [ /* test puzzles with encoded Penpa data */ ],
});
```

### Key Framework Abstractions

| Abstraction | Purpose |
|-------------|---------|
| `Context` | Wraps Z3's context object; provides `Or`, `Sum`, `And`, etc. |
| `Constraints` | Accumulates Z3 constraints; provides `int()`, `add()`, `solve()` |
| `Puzzle` | Parsed Penpa puzzle data: points, regions, parameters, lines |
| `Solution` | Output container: maps points to symbols for rendering |
| `ValueMap` | Map keyed by Point objects (using `toString()` for hashing) |
| `puzzle.points` | Point set with geometric queries (`vertexSharingPoints`, `lines`) |

### Solving Flow

```
User loads puzzle in Penpa UI
        ↓
Framework parses Penpa data into Puzzle object
        ↓
Framework creates Z3 Context and Constraints
        ↓
Solver function is called (declares constraints)
        ↓
cs.solve() invokes Z3 solver
        ↓
Z3 returns SAT + model, or UNSAT
        ↓
Solver reads model, populates Solution
        ↓
Framework renders Solution back in Penpa UI
```

### Solve Method

```typescript
// In ConstraintsImpl
async solve(arithsIt) {
    const result = await this.solver.check();
    if (result === "unsat") throw new Error("No solution");
    if (result === "unknown") throw new Error("Unknown");
    // Extract variable assignments from Z3 model
    return new Model(this.solver.model(), ariths);
}
```

---

## Hex Grid Support

A notable feature: the solver handles **hexagonal Star Battle** with zero code changes. The framework's geometry layer (`puzzle.points`, `vertexSharingPoints`, `lines`, `regions`) abstracts over grid topology, so the same constraint formulation works for square, hexagonal, and triangular grids.

The test samples include a hex Star Battle variant:

```typescript
{
    name: "Star Battle (hex)",
    parameters: "stars: 1",
    puzzle: "m=edit&p=7ZZRb9s2EMff/SkCPdOA...",
    answer: "m=edit&p=7Zbfb9s2EMff/VcUfKYB...",
}
```

This is a significant architectural advantage — the solver generalizes to any grid topology that the Penpa UI can represent.

---

## Comparison with Other Analyzed Solvers

| Dimension | hartez/starBattle (Go) | gjohnhazel/StarBattleSolver | nikoli-puzzle-solver (Z3) |
|-----------|----------------------|---------------------------|--------------------------|
| **Paradigm** | Imperative backtracking | Deduction/pattern matching | Declarative constraint solving |
| **Solver LOC** | ~350 lines | ~600 lines | ~30 lines |
| **Search engine** | Hand-written DFS | None (deduction only) | Z3 SMT solver |
| **Completeness** | Yes (will find solution if one exists) | No (fails if no pattern matches) | Yes (Z3 is complete for this theory) |
| **Correctness guarantee** | Depends on implementation | Depends on strategy correctness | Guaranteed by Z3 (modulo correct constraint encoding) |
| **Performance tuning** | Manual (variable ordering, pruning) | N/A | Z3-internal (CDCL, theory propagation) |
| **Grid topologies** | Square only | Square only (10x10) | Any (square, hex, triangular) |
| **Star count** | Configurable | Hardcoded to 2 | Configurable |
| **Grid size** | Configurable | Hardcoded to 10x10 | Any (limited by Z3 performance) |
| **Hint/explanation** | None | Yes (9 strategies) | None |
| **Puzzle generation** | None | None (manual drawing) | None |
| **Difficulty grading** | None | Implicit (strategy complexity) | None |
| **Unique solution check** | Not implemented | Not implemented | Not implemented (but easy to add) |
| **Dependencies** | None (stdlib only) | React, Zustand, etc. | Z3 (heavy — ~20MB WASM) |
| **Deployment** | CLI | Web app | Web app (with WASM Z3) |

### Performance Comparison

Direct benchmarks aren't available across these solvers, but we can reason about asymptotic behavior:

- **hartez**: Performance depends heavily on hand-tuned heuristics. Can be very fast with good pruning, but scales poorly without MRV/arc consistency. Hard 14x14 puzzles take seconds.
- **Z3-based**: Z3's CDCL solver is highly optimized for Boolean/integer constraint problems. Star Battle puzzles are extremely small by Z3 standards (100 variables, ~750 constraints). Expected solve time: milliseconds for any standard puzzle, though Z3 initialization and WASM overhead may dominate for small puzzles.

---

## Applicability to Our Goals

### For Solving: A Strong Reference Model

The Z3 approach gives us a **provably correct, complete solver** in minimal code. This is valuable as:

1. **A correctness oracle**: We can use a Z3-based solver to verify that our own solver implementations produce correct answers. Any disagreement indicates a bug in our code (assuming correct constraint encoding).
2. **A uniqueness checker**: By adding the negation of a found solution as a constraint and re-solving, we can check if a puzzle has a unique solution. This is critical for puzzle generation.
3. **A baseline implementation**: If we need a working solver quickly, the Z3 approach gets us there in ~30 lines.

**Adding uniqueness checking** would look like:

```typescript
// After finding first solution:
const solutionConstraint = Or(
    ...Array.from(grid).map(([p, v]) => 
        v.neq(model.get(v) ? 1 : 0)
    )
);
cs.add(solutionConstraint);
const model2 = await cs.solve(grid);  // If this succeeds, solution is NOT unique
```

### For Puzzle Generation: Z3 as a Verification Backend

A generation pipeline could use Z3 in two ways:

1. **Solution generation**: Declare only adjacency + row/col/region count constraints (no regions yet), find a valid star placement, then build regions around it.
2. **Uniqueness verification**: Given a puzzle (regions + rules), use Z3 to confirm exactly one solution exists. The enumerate-and-block approach above works but is slow for puzzles with many solutions. A SAT-based approach using "at most one solution" encoding would be more efficient.

### For Hints and Difficulty: Z3 Alone Is Insufficient

The Z3 approach has a fundamental limitation for our hint/difficulty goals: **Z3 provides no explanation of its reasoning**. It returns SAT or UNSAT, not "I deduced cell (3,4) is a star because of locked candidates in region 5."

For hints, we still need the deduction-based approach (like gjohnhazel's strategies). However, Z3 can augment a deduction engine:

- **Verifying deduction correctness**: After a deduction engine produces a hint, Z3 can verify it's actually correct.
- **Finding forced cells**: Z3 can quickly determine which cells are forced (must be star or must be empty in every valid solution) by testing each cell against both values. Forced cells are hint candidates.
- **Measuring difficulty**: If we build a deduction engine with progressively harder strategies, difficulty can be measured by which strategies are needed. Z3 serves as the fallback to confirm the puzzle is solvable when deduction strategies are exhausted.

### For Large Grids: Z3 Should Scale Well

Star Battle constraints are in the **pseudo-Boolean** fragment, which Z3 handles efficiently. The constraint count grows as O(N^2) (variables) and O(N^2) (adjacency pairs), which stays manageable even for large grids:

| Grid Size | Variables | Adjacency Constraints | Line + Region Constraints |
|-----------|-----------|----------------------|--------------------------|
| 10x10 | 100 | ~720 | 30 |
| 20x20 | 400 | ~3,000 | 60 |
| 50x50 | 2,500 | ~19,000 | 150 |
| 100x100 | 10,000 | ~78,000 | 300 |

Even 100x100 is tiny by Z3 standards. The bottleneck for large grids would be Z3's WASM initialization time and memory, not the solving itself.

### Dependency Trade-off

The main downside of Z3 is its **size**: the z3-solver WASM module is ~20MB. For a web application, this is significant. Options:

1. **Use Z3 server-side only**: Run Z3 on the backend for generation and uniqueness checking; use a lightweight custom solver on the client for interactive solving and hints.
2. **Lazy-load Z3**: Only download the WASM module when the user requests a feature that needs it (e.g., "check uniqueness").
3. **Use a lighter solver**: For pure solving (not generation/uniqueness), a well-optimized hand-written solver (like hartez's but improved) may be faster to load and fast enough to solve.

### Key Takeaways

1. **Z3 is the gold standard for correctness** — use it as our oracle and uniqueness checker
2. **The constraint formulation is the blueprint** — even if we don't use Z3, the three constraint types (adjacency, line sums, region sums) are exactly what any solver must enforce
3. **~30 lines for a complete solver** demonstrates the power of declarative constraint modeling — but the trade-off is zero explainability
4. **Hex grid support for free** is an architectural lesson: abstract over grid topology early, and solvers generalize automatically
5. **For our goals** (generation + hints + difficulty), Z3 is best used as a backend verification tool, not the primary user-facing solver

### Recommended Architecture Using Insights from All Three Solvers

```
┌─────────────────────────────────────────────────────┐
│                   Puzzle Generator                    │
│  1. Generate valid star placement (Z3 or backtrack)  │
│  2. Build regions around stars                        │
│  3. Verify unique solution (Z3 enumerate-and-block)  │
│  4. Grade difficulty (deduction engine)               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Deduction Engine                     │
│  Strategy-based solver (gjohnhazel-style)             │
│  - Basic eliminations (row/col/region full)           │
│  - Locked candidates (single-line regions)            │
│  - Shape patterns (T, L, rectangle)                   │
│  - Advanced: naked sets, pigeonhole, multi-unit       │
│  Provides: hints, explanations, difficulty scores     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Backtracking Solver (fallback)           │
│  hartez-style with improvements:                      │
│  - Undo stack instead of board copies                 │
│  - MRV variable ordering                              │
│  - Arc consistency propagation                        │
│  - "Enough room?" pruning                             │
│  Used when deduction engine stalls                    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                Z3 Verification Layer                  │
│  - Correctness oracle (verify solver outputs)         │
│  - Uniqueness checking (enumerate solutions)          │
│  - Forced cell detection (for hint generation)        │
│  Server-side only (avoids 20MB WASM on client)        │
└─────────────────────────────────────────────────────┘
```
