# Star Battle Solver - Architecture & Algorithm Analysis

> Analysis of [gjohnhazel/StarBattleSolver](https://github.com/gjohnhazel/StarBattleSolver)

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Star Battle Rules](#star-battle-rules)
- [Puzzle Creation (Generation)](#puzzle-creation-generation)
- [Puzzle Solving (Validation)](#puzzle-solving-validation)
- [Hint System (Deduction Engine)](#hint-system-deduction-engine)
- [Key Design Observations](#key-design-observations)
- [Potential Improvements](#potential-improvements)

---

## Project Overview

This is an interactive web application for **creating** and **solving** two-star Star Battle puzzles on a 10x10 grid. The project does **not** auto-generate random puzzles algorithmically — instead, it provides a **manual drawing tool** for users to define puzzle regions, and an **intelligent hint/deduction engine** that can analyze the current board state and suggest logical moves toward the solution.

The app operates in two modes:
- **Draw Mode**: Users click on cell boundaries to draw region walls, defining the puzzle layout.
- **Solve Mode**: Users place stars (double-tap) or X marks (single-tap) on cells, with access to a hint system.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite |
| State Management | Zustand (two stores: game state + solver state) |
| UI Components | Radix UI primitives, Tailwind CSS |
| Backend | Express.js (minimal — primarily serves the SPA) |
| Persistence | localStorage (client-side puzzle saves) |
| ORM (unused for puzzles) | Drizzle ORM (scaffolded but puzzles are client-only) |

---

## Repository Structure

```
├── client/src/
│   ├── components/game/
│   │   ├── grid.tsx           # 10x10 interactive grid renderer
│   │   ├── controls.tsx       # Mode switching, reset, validate, load examples
│   │   └── solver.tsx         # Hint/deduction UI panel
│   ├── lib/
│   │   ├── game-state.ts      # Zustand store: cells, boundaries, save/load
│   │   ├── solver-logic.ts    # Core deduction engine (29KB, ~600 lines)
│   │   ├── example-puzzles.ts # Two hardcoded example puzzles
│   │   └── utils.ts           # Tailwind merge utility
│   └── pages/
│       └── home.tsx           # Main page layout
├── server/
│   ├── index.ts               # Express server entry
│   ├── routes.ts              # API routes (minimal)
│   └── vite.ts                # Vite dev server integration
```

---

## Star Battle Rules

The app implements the standard **two-star** Star Battle variant:

1. **Grid**: 10x10 cells divided into regions by drawn boundaries.
2. **Stars per row**: Exactly 2 stars in every row.
3. **Stars per column**: Exactly 2 stars in every column.
4. **Stars per region**: Exactly 2 stars in every region.
5. **No adjacency**: No two stars may be adjacent — horizontally, vertically, **or diagonally** (king's move constraint).

Cell values: `0` = empty, `1` = star, `2` = X (eliminated).

---

## Puzzle Creation (Generation)

### Important Distinction: There Is No Procedural Generator

The repository does **not** contain an algorithmic puzzle generator that creates random valid puzzles. Puzzle creation is entirely **manual and user-driven**.

### How Puzzles Are Created

#### 1. Manual Drawing via Boundary Toggling

In Draw Mode, users define regions by toggling boundary walls between cells:

- **Data model** (`game-state.ts`):
  - `horizontal: boolean[][]` — 11 rows x 10 cols (walls between rows, including top/bottom edges)
  - `vertical: boolean[][]` — 10 rows x 11 cols (walls between columns, including left/right edges)
  - The outer edges (row 0, row 10 for horizontal; col 0, col 10 for vertical) default to `true` (always walls).

- **Boundary toggling** (`grid.tsx`): In draw mode, clicking between cells calls `toggleHorizontalBoundary(row, col)` or `toggleVerticalBoundary(row, col)`, which flips the boolean at that position.

#### 2. Region Detection via Flood Fill

Regions are **not explicitly defined** — they are **derived** from the boundary walls using a flood-fill algorithm in `findRegions()` (`solver-logic.ts`):

```typescript
const findRegions = (horizontal: boolean[][], vertical: boolean[][]): number[][] => {
  const grid = Array(10).fill(0).map(() => Array(10).fill(-1));
  let regionId = 0;

  const floodFill = (row: number, col: number, id: number) => {
    if (row < 0 || row >= 10 || col < 0 || col >= 10 || grid[row][col] !== -1) return;
    grid[row][col] = id;

    // Only flood into neighbors if no wall between them
    if (row > 0 && !horizontal[row][col])       floodFill(row - 1, col, id);  // Up
    if (row < 9 && !horizontal[row + 1][col])    floodFill(row + 1, col, id);  // Down
    if (col > 0 && !vertical[row][col])           floodFill(row, col - 1, id);  // Left
    if (col < 9 && !vertical[row][col + 1])       floodFill(row, col + 1, id);  // Right
  };

  for (let i = 0; i < 10; i++) {
    for (let j = 0; j < 10; j++) {
      if (grid[i][j] === -1) {
        floodFill(i, j, regionId);
        regionId++;
      }
    }
  }
  return grid;
};
```

**Key behavior**: The algorithm iterates over all cells. When it finds an unvisited cell (`-1`), it starts a new region and recursively fills all reachable cells (those not separated by a wall). This means regions are implicitly defined by the walls the user draws.

#### 3. Hardcoded Example Puzzles

Two example puzzles are provided in `example-puzzles.ts`, defined purely by their boundary arrays:

- **Puzzle 1 ("Simple Square")** — easy difficulty: Creates a grid divided by walls at rows 4 and 7, and columns 4 and 7, forming a roughly even grid of rectangular regions.
- **Puzzle 2 ("L-Shapes")** — medium difficulty: Walls at rows 3, 6, 8 and columns 3, 5, 8, creating irregular L-shaped regions.

Both are defined by directly constructing `horizontal` and `vertical` boolean arrays with specific wall positions.

#### 4. Custom Puzzle Saving

Users can save their drawn puzzles via `saveCustomPuzzle()`, which snapshots the current `GridState` (cells + boundaries) and appends it to the in-memory example list with a timestamped ID. Puzzles are also persisted to `localStorage` via the game state store.

---

## Puzzle Solving (Validation)

### How the App Checks Solutions

The solver does **not** brute-force search for a solution. Instead, it provides:

1. **Interactive solving**: Users manually place stars and X marks.
2. **Validation on demand**: The `validateGrid()` function checks if the current placement is a valid solution.
3. **Deduction-based hints**: The hint engine analyzes the current state and suggests logical next steps.

### Validation Algorithm (`game-state.ts: validateGrid()`)

```typescript
validateGrid: () => {
  const { cells } = get().gridState;

  // Check: every row and column must have exactly 2 stars
  for (let i = 0; i < 10; i++) {
    const rowStars = cells[i].filter(cell => cell === 1).length;
    const colStars = cells.map(row => row[i]).filter(cell => cell === 1).length;
    if (rowStars !== 2 || colStars !== 2) return false;
  }

  // Check: no two stars are adjacent (including diagonals)
  for (let i = 0; i < 10; i++) {
    for (let j = 0; j < 10; j++) {
      if (cells[i][j] === 1) {
        for (let di = -1; di <= 1; di++) {
          for (let dj = -1; dj <= 1; dj++) {
            if (di === 0 && dj === 0) continue;
            const ni = i + di, nj = j + dj;
            if (ni >= 0 && ni < 10 && nj >= 0 && nj < 10) {
              if (cells[ni][nj] === 1) return false;
            }
          }
        }
      }
    }
  }

  return true;
}
```

**Notable omission**: The validation checks row/column star counts and adjacency, but does **not** verify that each region contains exactly 2 stars. This appears to be a bug — region validation is missing from `validateGrid()`.

### Auto-Marking Adjacent Cells

When a user places a star (`toggleCell` with type `'star'`), the game automatically marks all 8 surrounding cells with an X (value `2`) if they are currently empty. This prevents the user from accidentally placing adjacent stars and provides visual feedback about eliminated positions.

---

## Hint System (Deduction Engine)

The hint system is the most sophisticated part of the codebase, implemented in `solver-logic.ts` (~600 lines). It uses a **strategy-based deduction approach** — not brute-force solving.

### Architecture

The system uses a separate Zustand store (`useSolver`) with:
- `deductions: Deduction[]` — ordered list of available logical deductions
- `currentDeduction: number` — index for user navigation
- Navigation functions: `nextDeduction()`, `prevDeduction()`
- `applyDeduction(index)` — executes or toggles a deduction
- `generateDeductions()` — runs all strategies and populates the list

### Deduction Data Model

```typescript
interface Deduction {
  type: 'basic' | 'pattern' | 'area' | 'multi-unit';
  description: string;       // Short title for the UI
  explanation: string;        // Detailed reasoning
  affected: Position[];       // Cells this deduction acts on
  apply: () => void;          // Function to modify game state
  certainty: 'definite' | 'likely';
  isApplied?: boolean;        // Toggle state for undo
}
```

### Generation Pipeline

When the user opens the hint panel, `generateDeductions()` is called:

```typescript
generateDeductions: () => {
  // 1. Get current board state from game store
  const { cells, horizontal, vertical } = useGameState.getState().gridState;

  // 2. Check that boundaries exist (puzzle has been drawn)
  if (!hasRegions) { /* show "draw first" message */ return; }

  // 3. Derive regions from boundaries
  const regions = findRegions(horizontal, vertical);

  // 4. Run ALL strategy functions
  const deductions = [
    ...findBasicDeductions(cells),
    ...findSandwichPatterns(cells, regions),
    ...findLockedSets(cells, regions),
    ...findMultiUnitConstraints(cells, regions),
    ...findSquareRegions(cells, regions),
    ...findTShapedRegions(cells, regions),
    ...findLShapedRegions(cells, regions),
    ...findSingleLineRegions(cells, regions),
    ...analyzeRegions(cells, horizontal, vertical),
    ...findSixCellRectangles(cells, regions),
  ];

  // 5. Sort by complexity: basic → pattern → area → multi-unit
  deductions.sort((a, b) => typeOrder[a.type] - typeOrder[b.type]);

  // 6. Fallback: if no deductions found, add a general tip
}
```

### Strategy Catalog (9 Strategies)

#### 1. `findBasicDeductions(cells)` — Type: `basic`

**What it detects**: A row that already has 1 star and only 1 empty cell remaining.

**Logic**: For each row, count stars and empty cells. If `starCount === 1` and `emptyCount === 1`, the last empty cell must be a star.

**Limitation**: Only checks rows, not columns. Only triggers when exactly 1 empty cell remains.

---

#### 2. `findSandwichPatterns(cells, regions)` — Type: `pattern`

**What it detects**: When a row has exactly 1 star and only 1 valid position remains for the second star due to spacing/adjacency constraints.

**Logic**:
1. Find rows with exactly 1 star placed.
2. For each empty cell at least 2 columns away from the existing star, check if placing a star there would conflict with any star in the same row, column, or region (via `getRelatedCells()`).
3. If only 1 valid position exists, it's forced.

**Note**: Despite the name "sandwich," this doesn't detect the classic sandwich pattern. It's more of an "elimination by adjacency + region constraints" strategy.

---

#### 3. `findLockedSets(cells, regions)` — Type: `area`

**What it detects**: Regions where the number of remaining empty cells equals the number of stars still needed.

**Logic**: For each region, calculate `requiredStars = Math.floor(regionCells.length / 5) * 2`. If `emptyCount === requiredStars - existingStars`, all empty cells must be stars.

**Issue**: The formula `Math.floor(size / 5) * 2` for required stars is unconventional. In standard two-star Star Battle, every region needs exactly 2 stars regardless of size. This formula would give 0 stars for regions with < 5 cells and 2 for regions with 5-9 cells.

---

#### 4. `findMultiUnitConstraints(cells, regions)` — Type: `multi-unit`

**What it detects**: Cells forced to be stars because all related cells (same row, column, and region) are blocked.

**Logic**: For each empty cell, gather all cells sharing its row, column, or region. If every related cell is already blocked (value `2`) except the cell itself, it must be a star.

---

#### 5. `findSquareRegions(cells, regions)` — Type: `pattern`

**What it detects**: The center cell of a 3x3 (or near-3x3) region must be empty.

**Logic**: For regions of 8 or 9 cells that fit in a 3x3 bounding box, the center cell can't hold a star because any star placed there would be adjacent to all 8 surrounding cells, making it impossible to place a second star in the region.

---

#### 6. `findTShapedRegions(cells, regions)` — Type: `pattern`

**What it detects**: T-shaped 4-cell regions where star placement is forced.

**Logic**:
1. For each 4-cell region, analyze the distribution of cells across rows and columns.
2. Detect T-shapes: one row/column has 2 cells (the bar), others have 1 each.
3. Also checks for extended T-shapes with 3-cell columns and 1-cell branches.
4. When a T-shape is found, stars are forced at the junction cell and the stem tip, because adjacency rules eliminate all other pairings.

**Note**: This is the most complex strategy with ~100 lines of detection logic.

---

#### 7. `findLShapedRegions(cells, regions)` — Type: `pattern`

**What it detects**: L-shaped 4-cell regions where the far end of the long side must contain a star.

**Logic**:
1. For each 4-cell region, check if it forms an L-shape: a 3-cell line with 1 cell extending perpendicular at one end.
2. Identify the corner cell (where the bend is) and the edge cell (far end of the long side).
3. The edge cell is forced to be a star — placing stars at the corner and its adjacent cell would violate adjacency.

---

#### 8. `findSingleLineRegions(cells, regions)` — Type: `pattern`

**What it detects**: When an entire region fits in a single row or column, all other cells in that row/column can be eliminated.

**Logic**: If all cells in a region share the same row, then the region's 2 required stars account for the row's full star quota. Therefore, all other cells in that row (from different regions) can be marked as X. Same logic applies for columns.

**This is one of the most powerful standard Star Battle deduction techniques.**

---

#### 9. `findSixCellRectangles(cells, regions)` — Type: `pattern`

**What it detects**: In a 2x3 or 3x2 rectangular region, the center cells must be empty.

**Logic**: For 6-cell regions with a 2x3 or 3x2 bounding box:
- In a 3x2 rectangle: the two middle-row cells are eliminated.
- In a 2x3 rectangle: the two middle-column cells are eliminated.

**Reasoning**: If a star were placed on a center cell, it would be adjacent to too many cells, making it impossible to place the second star within the same region while respecting adjacency.

---

#### 10. `analyzeRegions(cells, horizontal, vertical)` — Type: `area`

**What it detects**: Two sub-strategies:

**Small region (3 cells)**: A 3-cell region must have 2 stars. Due to adjacency, they can only go at the "endpoints" — cells connected to only 1 neighbor within the region (identified by `findEndpoints()` which counts boundary-free connections).

**General region fill**: Same as `findLockedSets` — when remaining empty cells exactly equals needed stars.

---

### Hint Presentation Flow

1. User clicks "Hints" button → `Solver` component mounts → `useEffect` calls `generateDeductions()`.
2. All strategies run against current board state; results are sorted by type complexity.
3. Hints are displayed one at a time in a card UI with:
   - **Type badge**: Color-coded (blue=basic, purple=pattern, green=area, orange=multi-unit)
   - **Certainty indicator**: "Certain" (definite) or "Possible" (likely)
   - **Description**: Short title of the deduction
   - **Explanation**: Human-readable reasoning
   - **Affected positions**: Grid coordinates of relevant cells
4. User navigates with Previous/Next buttons.
5. "Apply Deduction" button executes the deduction's `apply()` function, which calls `toggleCell()` on the game state to place stars or X marks. The button toggles to "Remove Deduction" (though true undo is limited since `toggleCell` is a toggle).

---

## Key Design Observations

### Strengths

1. **Clean separation of concerns**: Game state and solver logic are in separate Zustand stores, communicating through `getState()`.
2. **Deduction-based hints**: Rather than just showing the answer, the system teaches solving strategies with explanations — good for learning.
3. **Progressive hint complexity**: Sorting by type (basic → pattern → area → multi-unit) gives simpler hints first.
4. **Implicit region detection**: The flood-fill approach from boundaries is elegant — users draw walls, regions are auto-derived.

### Weaknesses & Bugs

1. **No puzzle generation**: Despite the README title "Star Battle Puzzle Solver," there's no algorithm to generate valid puzzles from scratch. Puzzles are either manually drawn or loaded from 2 hardcoded examples.

2. **Validation doesn't check regions**: `validateGrid()` verifies row/column star counts and adjacency but **never checks that each region has exactly 2 stars**. This means an invalid solution (correct rows/columns but wrong region counts) would be accepted.

3. **Incorrect `requiredStars` formula**: `findLockedSets()` uses `Math.floor(regionCells.length / 5) * 2`, which would compute 0 required stars for regions smaller than 5 cells. In two-star Star Battle, every region needs exactly 2 stars regardless of size.

4. **Hints are stateless**: `generateDeductions()` runs all strategies from scratch each time. It doesn't track which deductions have already been applied or adapt to partial progress. This can lead to redundant or contradictory hints if the board state changes between hint generations.

5. **No backtracking solver**: The app has no complete solver that can find the solution to a given puzzle. The deduction engine only handles specific known patterns — if none apply, it gives a generic "no deductions available" message. A complete solver would require backtracking/constraint propagation.

6. **Missing column-based basic deductions**: `findBasicDeductions()` only checks rows, not columns. A symmetric column check would double its effectiveness.

7. **T-shape detection has dead code**: The `findTShapedRegions` function has two overlapping detection approaches — the first uses row/column count analysis, and then there's additional code checking `leftCol`/`middleColCells`/`rightColCells` that can produce contradictory results since `middleCell` and `stemCell` may be overwritten.

---

## Potential Improvements

1. **Add a puzzle generator**: Implement a constraint-satisfaction generator that:
   - Places 20 stars on the grid respecting row/column/adjacency rules
   - Partitions the grid into 10 regions, each containing exactly 2 stars
   - Validates the puzzle has a unique solution

2. **Add a complete solver**: Implement backtracking with constraint propagation to:
   - Verify puzzle uniqueness
   - Provide a "show solution" feature
   - Validate that user-drawn puzzles are solvable

3. **Fix region validation**: Add region star count checking to `validateGrid()`.

4. **Fix `requiredStars` formula**: Replace `Math.floor(size / 5) * 2` with a constant `2` for two-star puzzles.

5. **Add more deduction strategies**: Common techniques not yet implemented:
   - Column-based basic deductions
   - Pigeonhole principle across region-row/region-column intersections
   - "Two regions in two rows" type constraints
   - Recursive constraint propagation (when one deduction enables another)
