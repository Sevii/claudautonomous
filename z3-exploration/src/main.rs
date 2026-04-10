use z3::ast::{Ast, Bool, Int};
use z3::{SatResult, Solver};

fn main() {
    // --- Example 1: Basic constraint satisfaction ---
    println!("=== Example 1: Apple division ===");
    basic_constraint_satisfaction();

    // --- Example 2: Sudoku-style logic puzzle ---
    println!("\n=== Example 2: 4x4 Sudoku ===");
    mini_sudoku();

    // --- Example 3: Boolean satisfiability ---
    println!("\n=== Example 3: Boolean SAT ===");
    boolean_sat();

    // --- Example 4: Proving validity (unsatisfiability of negation) ---
    println!("\n=== Example 4: Proving a theorem ===");
    prove_theorem();
}

/// Demonstrates integer constraints and extracting model values.
///
/// Three friends split 30 apples: each gets >= 1, a >= b >= c.
fn basic_constraint_satisfaction() {
    let a = Int::new_const("a");
    let b = Int::new_const("b");
    let c = Int::new_const("c");
    let one = Int::from_i64(1);
    let thirty = Int::from_i64(30);

    let solver = Solver::new();

    // a + b + c == 30
    solver.assert(&Int::add(&[&a, &b, &c]).eq(&thirty));
    // each >= 1
    solver.assert(&a.ge(&one));
    solver.assert(&b.ge(&one));
    solver.assert(&c.ge(&one));
    // a >= b >= c
    solver.assert(&a.ge(&b));
    solver.assert(&b.ge(&c));

    match solver.check() {
        SatResult::Sat => {
            let model = solver.get_model().unwrap();
            let a_val = model.eval(&a, true).unwrap();
            let b_val = model.eval(&b, true).unwrap();
            let c_val = model.eval(&c, true).unwrap();
            println!("SAT: a={a_val}, b={b_val}, c={c_val}");
        }
        other => println!("Unexpected result: {other:?}"),
    }
}

/// Solves a 4x4 Sudoku using Z3 integer constraints.
fn mini_sudoku() {
    let solver = Solver::new();

    // Create a 4x4 grid of integer variables
    let grid: Vec<Vec<Int>> = (0..4)
        .map(|r| {
            (0..4)
                .map(|c| Int::new_const(format!("cell_{r}_{c}")))
                .collect()
        })
        .collect();

    let one = Int::from_i64(1);
    let four = Int::from_i64(4);

    // Each cell is between 1 and 4
    for row in &grid {
        for cell in row {
            solver.assert(&cell.ge(&one));
            solver.assert(&cell.le(&four));
        }
    }

    // Each row has distinct values
    for row in &grid {
        let refs: Vec<&Int> = row.iter().collect();
        solver.assert(&Int::distinct(&refs));
    }

    // Each column has distinct values
    for c in 0..4 {
        let col: Vec<&Int> = (0..4).map(|r| &grid[r][c]).collect();
        solver.assert(&Int::distinct(&col));
    }

    // Each 2x2 box has distinct values
    for br in [0, 2] {
        for bc in [0, 2] {
            let block: Vec<&Int> = vec![
                &grid[br][bc],
                &grid[br][bc + 1],
                &grid[br + 1][bc],
                &grid[br + 1][bc + 1],
            ];
            solver.assert(&Int::distinct(&block));
        }
    }

    // Pre-filled clues:
    //  _ 2 _ _
    //  _ _ _ 3
    //  _ _ _ _
    //  4 _ _ _
    solver.assert(&grid[0][1].eq(&Int::from_i64(2)));
    solver.assert(&grid[1][3].eq(&Int::from_i64(3)));
    solver.assert(&grid[3][0].eq(&Int::from_i64(4)));

    match solver.check() {
        SatResult::Sat => {
            let model = solver.get_model().unwrap();
            for r in 0..4 {
                let row: Vec<String> = (0..4)
                    .map(|c| format!("{}", model.eval(&grid[r][c], true).unwrap()))
                    .collect();
                println!("  {}", row.join(" "));
            }
        }
        SatResult::Unsat => println!("No solution exists."),
        SatResult::Unknown => println!("Solver returned unknown."),
    }
}

/// Demonstrates boolean satisfiability.
fn boolean_sat() {
    let x = Bool::new_const("x");
    let y = Bool::new_const("y");
    let z = Bool::new_const("z");

    let solver = Solver::new();

    // (x OR y) AND (NOT x OR z) AND (NOT y OR NOT z)
    solver.assert(&Bool::or(&[&x, &y]));
    solver.assert(&Bool::or(&[&x.not(), &z]));
    solver.assert(&Bool::or(&[&y.not(), &z.not()]));

    match solver.check() {
        SatResult::Sat => {
            let model = solver.get_model().unwrap();
            let x_val = model.eval(&x, true).unwrap();
            let y_val = model.eval(&y, true).unwrap();
            let z_val = model.eval(&z, true).unwrap();
            println!("SAT: x={x_val}, y={y_val}, z={z_val}");
        }
        other => println!("Result: {other:?}"),
    }
}

/// Proves that for all integers x: (x >= 0 AND x < 5) implies (x < 10).
/// We assert the negation and show it's unsatisfiable.
fn prove_theorem() {
    let x = Int::new_const("x");
    let zero = Int::from_i64(0);
    let five = Int::from_i64(5);
    let ten = Int::from_i64(10);

    let solver = Solver::new();

    // Negate the theorem: exists x such that (x >= 0 AND x < 5 AND x >= 10)
    let premise = Bool::and(&[&x.ge(&zero), &x.lt(&five)]);
    let negated_conclusion = x.ge(&ten);
    solver.assert(&Bool::and(&[&premise, &negated_conclusion]));

    match solver.check() {
        SatResult::Unsat => {
            println!("PROVED: (x >= 0 && x < 5) implies (x < 10) for all integers x");
        }
        SatResult::Sat => {
            let model = solver.get_model().unwrap();
            println!("COUNTEREXAMPLE found: x={}", model.eval(&x, true).unwrap());
        }
        SatResult::Unknown => println!("Solver returned unknown."),
    }
}
