# hartez/starBattle - Algorithm & Architecture Analysis

> Analysis of [hartez/starBattle](https://github.com/hartez/starBattle)
> Companion blog series: [ezhart.com](https://ezhart.com/posts/star-battle-part-1) (Parts 1-5)

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Puzzle Representation](#puzzle-representation)
- [Core Solving Algorithm](#core-solving-algorithm)
- [Constraint Propagation (Forward Checking)](#constraint-propagation-forward-checking)
- [Validity Checking & Pruning](#validity-checking--pruning)
- [Parallel Solving](#parallel-solving)
- [Performance Benchmarks](#performance-benchmarks)
- [Key Data Structures](#key-data-structures)
- [Applicability to Our Goals](#applicability-to-our-goals)

---

## Project Overview

This is a **solver-only** Star Battle implementation written in Go as a learning project. It reads puzzle definitions from text files and solves them via recursive backtracking with constraint propagation. There is **no puzzle generator**, **no hint system**, and **no difficulty grading**. The project's value for our purposes is in understanding the solving algorithm's performance characteristics across different grid sizes, its constraint propagation techniques, and the parallelization approach.

The repository includes a companion 5-part blog series that documents the evolution from a naive brute-force solver to an optimized parallel solver, with detailed performance measurements at each stage.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Go 1.23.3 |
| Dependencies | None (stdlib only) |
| Concurrency | goroutines, channels, sync.WaitGroup, context.Context |
| Profiling | pprof + Graphviz |
| Testing | Go standard `testing` package |

---

## Repository Structure

```
hartez/starBattle/
├── main.go              # CLI entry point (sequential + parallel modes)
├── board.go             # Board type, parsing, solving, constraint propagation (~350 lines)
├── square.go            # Square enum type (UNKNOWN, STAR, NOTSTAR)
├── board_test.go        # Comprehensive test suite (parsing, validation, solving)
├── benchmark_test.go    # Performance tests across 3 difficulty levels
├── go.mod               # Module definition (no external deps)
├── 5_1.txt              # 5x5, 1-star puzzle
├── 6_1.txt              # 6x6, 1-star puzzle
├── 8_1.txt              # 8x8, 1-star puzzle
├── 10_2.txt             # 10x10, 2-star puzzle
├── 10_2_2.txt           # 10x10, 2-star puzzle (variant)
├── 14_3.txt             # 14x14, 3-star puzzle
├── 14_3_2.txt ~ 14_3_7.txt  # Six more 14x14/3-star variants
├── broken_puzzle.txt    # Intentionally unsolvable puzzle (for testing)
├── LICENSE
└── README.md
```

---

## Puzzle Representation

### File Format

Puzzles are stored as flat CSV files with an optional star-count prefix:

```
# 5x5, 1-star (default 1 star when no prefix)
1,1,1,2,2,3,1,1,2,2,3,1,1,2,2,3,3,1,4,4,3,3,5,5,4

# 14x14, 3-star (prefix "3*" specifies star count)
3*1,2,2,2,2,3,4,4,4,4,4,5,5,5,1,1,2,2,3,3,4,4,5,4,4,5,5,5,...

# 10x10, 2-star
2*1,2,2,2,3,3,3,3,4,4,1,1,1,2,2,2,3,4,4,4,...
```

### Parsing Algorithm (`Parse()`)

1. Read file contents
2. Check for `N*` prefix to extract star count (default: 1)
3. Split remaining data by commas
4. Derive grid size as `sqrt(len(values))` — the grid must be square
5. Assign each cell to its region (regions are 1-indexed in files, converted to 0-indexed)

This format is compact and supports arbitrary grid sizes and star counts. The grid size is inferred rather than declared, which is elegant but means malformed files with non-square cell counts would silently produce incorrect boards.

### Internal Board Representation

```go
type Board struct {
    size    int        // Grid dimension (N for NxN)
    stars   int        // Stars required per row/col/region
    squares []Square   // Flat array of size*size cells
    regions [][]int    // regions[i] = list of flat indices in region i
}

type Square int
const (
    UNKNOWN  Square = iota  // 0 - not yet decided
    STAR                     // 1 - star placed
    NOTSTAR                  // 2 - eliminated
)
```

The board uses a **flat 1D array** indexed by `row * size + col`. Regions are stored as slices of flat indices, meaning region lookup for a given cell requires scanning all region slices (O(N) per lookup via `slices.Contains`).

---

## Core Solving Algorithm

### Approach: Recursive Backtracking (DFS) with Forward Checking

The solver uses a classic depth-first search with binary branching: for each unknown cell, try STAR then try NOTSTAR.

```go
func (board Board) Solve() (bool, Board) {
    // 1. Prune: check if current state is still valid
    if !board.isValid() {
        return false, board
    }

    // 2. Terminal: check if we have a complete solution
    if board.hasEnoughStars() {
        return true, board
    }

    // 3. Select: find next undecided cell (first UNKNOWN, left-to-right, top-to-bottom)
    nextRow, nextCol, err := board.findEmptySquare()
    if err != nil {
        return false, board
    }

    // 4. Branch A: try placing a STAR
    nextBoard := board.copy()
    nextBoard.setValue(nextRow, nextCol, STAR)
    nextBoard.eliminateSquares(nextRow, nextCol)  // Forward checking
    solved, solvedBoard := nextBoard.Solve()
    if solved {
        return true, solvedBoard
    }

    // 5. Branch B: try marking as NOTSTAR
    nextBoard = board.copy()
    nextBoard.setValue(nextRow, nextCol, NOTSTAR)
    return nextBoard.Solve()
}
```

### Key Characteristics

- **Variable ordering**: Static — always picks the first UNKNOWN cell in row-major order. No heuristics like "most constrained first" (MRV) or "most constraining first" (degree heuristic).
- **Value ordering**: Always tries STAR before NOTSTAR. No dynamic value ordering.
- **State management**: Full board copy on each branch. This is memory-intensive but avoids complex undo logic.
- **Forward checking**: When a STAR is placed, `eliminateSquares()` immediately marks forced NOTSTAR cells. When NOTSTAR is placed, no propagation occurs.

### Search Space

For an NxN grid, the naive search space is 2^(N*N) since each cell is either STAR or NOTSTAR. The constraint propagation dramatically reduces this in practice, but the worst case remains exponential.

---

## Constraint Propagation (Forward Checking)

When a star is placed at `(row, col)`, four elimination rules fire:

### 1. Row Elimination (`eliminateSquaresInRow`)

If the row now contains `board.stars` stars, mark all remaining UNKNOWN cells in that row as NOTSTAR.

```go
func (board Board) eliminateSquaresInRow(row int) {
    starCount, _ := board.countInRow(row)
    if starCount == board.stars {
        for col := range board.size {
            if value, _ := board.value(row, col); value == UNKNOWN {
                board.setValue(row, col, NOTSTAR)
            }
        }
    }
}
```

### 2. Column Elimination (`eliminateSquaresInColumn`)

Same logic applied to the column.

### 3. Adjacency Elimination (`eliminateAdjacentSquares`)

All 8 neighbors (king's move) of the placed star are marked NOTSTAR:

```go
func (board Board) eliminateAdjacentSquares(row int, col int) {
    for r := row - 1; r <= row+1; r++ {
        for c := col - 1; c <= col+1; c++ {
            if r >= 0 && c >= 0 && c < board.size && r < board.size {
                if value, _ := board.value(r, c); value == UNKNOWN {
                    board.setValue(r, c, NOTSTAR)
                }
            }
        }
    }
}
```

### 4. Region Elimination (`eliminateSquaresInRegion`)

If the region containing the placed star now has `board.stars` stars, mark all remaining UNKNOWN cells in that region as NOTSTAR.

### What's NOT Implemented

- **Arc consistency / AC-3**: No propagation cascade — eliminations don't trigger further eliminations.
- **Naked/hidden sets**: No detection of forced placements within partially-filled rows/cols/regions.
- **Locked candidates**: No detection of region-line intersections that force eliminations.
- **Constraint propagation on NOTSTAR placement**: When a cell is marked NOTSTAR, no check is made whether this forces a star elsewhere (e.g., if a row now has only N unknown cells remaining and needs N stars).

These missing techniques represent significant opportunities for optimization, especially for larger grids.

---

## Validity Checking & Pruning

The `isValid()` function performs early termination checks:

```go
func (board Board) isValid() bool {
    for row := range boardSize {
        stars, notStars := board.countInRow(row)
        if stars > requiredStars { return false }           // Too many stars
        if requiredStars > boardSize-notStars { return false } // Not enough room for remaining stars
    }
    // Same checks for columns and regions
    ...
}
```

### Pruning Rules

For each row, column, and region:

1. **Over-constraint**: If star count exceeds the required number → invalid
2. **Under-constraint**: If `required_stars > (total_cells - notstar_cells)` → invalid (not enough room for the remaining stars, even if all remaining UNKNOWN cells were stars)

This second rule is the most powerful pruning heuristic. The blog series documents that adding it reduced solve time for a hard 14x14 puzzle from ~25 seconds to under 1 second.

### Evolution of `isValid()` (from blog series)

| Version | What it checks | Hard puzzle time |
|---------|---------------|-----------------|
| V1 (naive) | Stars > limit, adjacent stars | ~23 sec |
| V2 (+elimination) | Same + forward elimination | ~1 min 46 sec* |
| V3 (-adjacency check) | Removed redundant adjacency (handled by elimination) | ~25 sec |
| V4 (+room check) | Added "enough room?" check | < 1 sec |

*V2 was slower because the elimination logic was added but `isValid()` still redundantly checked adjacency, which pprof identified as a bottleneck.

---

## Parallel Solving

### Architecture

The parallel solver spawns a goroutine for each branch of the search tree:

```go
func (board Board) SolveParallel() (bool, *Board) {
    solutionChannel := make(chan *Board)
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    var wg sync.WaitGroup
    wg.Add(1)
    go board.solveParallel(solutionChannel, &wg, ctx)
    go func() {
        wg.Wait()
        solutionChannel <- nil  // Signal: all work done, no solution
    }()
    solution := <-solutionChannel
    return solution != nil, solution
}
```

### Concurrency Mechanisms

| Mechanism | Purpose |
|-----------|---------|
| `context.Context` + cancel | Stop all goroutines when first solution is found |
| `sync.WaitGroup` | Track when all goroutines have finished (for unsolvable puzzles) |
| `chan *Board` | Communicate solution from any goroutine back to caller |
| `select` statement | Check for cancellation before each recursive call |

### Goroutine Spawning

Each node in the search tree spawns two goroutines:

```go
func (board Board) solveParallel(solution chan *Board, wg *sync.WaitGroup, ctx context.Context) {
    defer wg.Done()
    select {
    case <-ctx.Done():
        return  // Another goroutine found the solution
    default:
        // ... validity check, star check ...

        // Branch A: STAR
        nextBoard := board.copy()
        nextBoard.setValue(nextRow, nextCol, STAR)
        nextBoard.eliminateSquares(nextRow, nextCol)
        wg.Add(1)
        go nextBoard.solveParallel(solution, wg, ctx)

        // Branch B: NOTSTAR
        nextBoard = board.copy()
        nextBoard.setValue(nextRow, nextCol, NOTSTAR)
        wg.Add(1)
        go nextBoard.solveParallel(solution, wg, ctx)
    }
}
```

### Scalability Concerns

- **Goroutine explosion**: Every branch spawns 2 goroutines. For a 14x14 grid (196 cells), this can create millions of goroutines before pruning kicks in. Go's lightweight goroutines handle this better than OS threads, but it's still significant.
- **No work stealing or bounded parallelism**: There's no goroutine pool or limit. The Go scheduler handles distribution, but memory pressure from board copies + goroutine stacks could be a bottleneck for very large grids.
- **Copy overhead**: Each goroutine gets its own board copy, which includes copying the squares array and region slices.

### Parallel Performance (from blog)

| Puzzle | Sequential | Parallel | Speedup |
|--------|-----------|----------|---------|
| Easy 14x14 | < 1 sec | < 1 sec | None (overhead dominates) |
| Hard 14x14 | ~10 sec | ~5 sec | ~2x on 8-core laptop |

Parallelism only helps for puzzles that are already slow to solve sequentially. The overhead of goroutine creation and board copying negates benefits for easy puzzles.

---

## Performance Benchmarks

### Measured Performance (from blog series, final optimized version)

| Puzzle | Size | Stars | Sequential | Parallel |
|--------|------|-------|-----------|----------|
| 5_1.txt | 5x5 | 1 | ~609 microseconds | N/A |
| 10_2.txt | 10x10 | 2 | ~510 ms | N/A |
| 14_3.txt | 14x14 | 3 | < 1 sec | < 1 sec |
| Hard 14x14 variant | 14x14 | 3 | ~8.7 sec | ~5 sec |

### Optimization Impact (hard 14x14 variant)

| Optimization Stage | Time |
|---|---|
| Naive backtracking | > 11 minutes |
| + Forward elimination on star placement | ~1 min 46 sec |
| + Remove redundant adjacency validation | ~25 sec |
| + "Enough room?" pruning in isValid() | ~8.7 sec |
| + Parallel solving | ~5 sec |

The single biggest win (~25 sec → <1 sec for the standard hard puzzle) came from the "enough room?" pruning rule, which detects dead-end branches where remaining UNKNOWN cells can't satisfy the star quota.

---

## Key Data Structures

### Board

```go
type Board struct {
    size    int        // N for NxN grid
    stars   int        // Stars per row/col/region
    squares []Square   // Flat [size*size]Square, indexed by row*size+col
    regions [][]int    // regions[i] = slice of flat indices belonging to region i
}
```

**Trade-offs**:
- Flat array is cache-friendly for row iteration
- Region lookup is O(N) per cell (linear scan through all region slices) — this is a scalability issue
- Full board copy on each recursion branch — memory O(depth * N^2)

### Square

```go
type Square int  // UNKNOWN=0, STAR=1, NOTSTAR=2
```

Simple 3-state enum. Using `int` rather than a bitfield means no packing — each cell uses a full machine word.

---

## Applicability to Our Goals

### For Generating Large Star Battle Puzzles

**What we can learn:**
- The solver's architecture (backtracking + forward checking) is the standard approach and will be needed as a sub-component of any generator (to verify solutions and uniqueness)
- The "enough room?" pruning is essential and should be included from the start
- Puzzle file format (`N*region1,region2,...`) is clean and worth adopting

**What's missing for generation:**
- No puzzle generator at all — we need to build one
- No region generation algorithm — regions must come from somewhere
- No uniqueness checking — a generator needs to verify exactly one solution exists
- No difficulty assessment — can't grade puzzles without understanding what makes them hard

### For Supporting Hints

**What we can learn:**
- The solver finds solutions but provides no intermediate reasoning. For hints, we need a **logic-based solver** that can explain each step (see gjohnhazel/StarBattleSolver analysis for hint strategies).
- The elimination rules (`eliminateSquares*`) are the simplest hint type: "this row/col/region is full, so remaining cells are not stars"

**What's missing for hints:**
- No deduction engine — just brute-force search
- No strategy identification — can't say "this cell is forced because of naked pair in row 3"
- No step-by-step solution path

### For Variable Difficulty

**What we can learn:**
- Grid size + star count is the primary difficulty axis: 5x5/1-star is trivial, 14x14/3-star is hard
- Even within the same size, different region layouts create vastly different solve times (< 1 sec vs ~10 sec for 14x14/3-star)
- Region layout is therefore a major factor in puzzle difficulty

**What's missing:**
- No difficulty metrics or scoring
- No control over what solving techniques are needed
- No way to generate puzzles that require specific deduction patterns

### Scalability Assessment for Large Grids

| Concern | Impact | Mitigation Needed |
|---------|--------|------------------|
| O(N) region lookup | Severe for N > 20 | Use cell→region lookup table (O(1)) |
| Full board copy per branch | Memory blowup for large N | Use undo stack instead of copy |
| No MRV heuristic | Explores many dead branches | Implement "most constrained variable first" |
| No arc consistency | Misses forced propagations | Implement AC-3 or similar |
| Static variable ordering | Suboptimal search tree | Order by region size, row/col fill level |
| Goroutine explosion | Memory pressure | Use bounded worker pool |

### Recommendations for Our Implementation

1. **Adopt the backtracking + forward checking core** but replace board copying with an undo stack
2. **Add a cell→region lookup table** (O(1) instead of O(N))
3. **Implement MRV heuristic** for variable ordering (choose the most constrained unfilled cell next)
4. **Add arc consistency propagation** so eliminations cascade
5. **Build a logic-based solver layer** on top for hints and difficulty grading
6. **Use solve technique requirements** as the difficulty metric: puzzles solvable by basic elimination alone are "easy"; those requiring advanced deductions are "hard"
7. **For generation**: start with a valid star placement, build regions around it, then verify uniqueness and difficulty
