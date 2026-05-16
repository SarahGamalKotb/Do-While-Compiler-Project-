# Do-While Compiler Project Report
## CET313 — Theory of Computing | Spring 2026

**Team 24**
| Name | Student ID |
|------|------------|
| Sarah Gamal Mohamed | 230104240 |
| Ahd Mohamed Elazeb | 230105494 |
| Battol Mohamed Galal | 240102737 |

---

## 1. What We Built

We built a compiler that takes a Do-While statement written in C-style code and processes it through four phases: **Lexical Analysis**, **Syntax Analysis** (with a CFG and Shift-Reduce parser), **Semantic Analysis**, and **Assembly Code Generation**.

The input to our compiler looks like this:

```c
int i;
i = 1;
do {
    printf("%d\n", i);
    i++;
}
while (i < 5);
```

The compiler runs automatically and produces five output files: `lexeme_table.txt`, `cfg.txt`, `syntax_tree.txt`, `semantic.txt`, and `assembly.txt`.

---

## 2. Design Flowchart (Pseudocode)

```
START
│
├─ Read source code from code.txt
│
├─ PHASE 1 — LEXICAL ANALYZER
│   ├─ Loop through each character
│   ├─ Skip whitespace
│   ├─ If letter/underscore  → collect word → KEYWORD or IDENTIFIER
│   ├─ If digit              → collect digits → NUMBER
│   ├─ If two-char operator  → check ++ -- == != <= >= → OPERATOR
│   ├─ If single operator    → OPERATOR
│   ├─ If separator          → SEPARATOR
│   └─ Output: Lexeme Table
│
├─ CFG DEFINITION
│   └─ Define grammar rules for DoWhileStmt (hardcoded in array)
│
├─ PHASE 2 — SYNTAX ANALYZER (Bottom-Up Shift-Reduce)
│   ├─ Separate pre-do tokens (declarations, init assignment)
│   ├─ Main loop:
│   │   ├─ Try to REDUCE (check stack top against all grammar rules)
│   │   └─ If no reduction → SHIFT (push next token onto stack)
│   ├─ Final reduce → DoWhileStmt
│   └─ Output: Parse log + Syntax Tree
│
├─ PHASE 3 — SEMANTIC ANALYZER
│   ├─ Pass 1: Collect all declared variables → Symbol Table
│   ├─ Pass 2: Check each identifier usage
│   │   ├─ Is it declared? If not → ERROR
│   │   ├─ Is ++ or -- used on declared var? If not → ERROR
│   │   └─ Is there division by zero? → ERROR
│   └─ Output: semantic.txt (PASSED or FAILED)
│
├─ PHASE 4 — ASSEMBLY GENERATOR
│   ├─ Read variable name from symbol table
│   ├─ Find initial value from lexeme table (ID = NUMBER pattern)
│   ├─ Find comparison operator and value (from do-while condition)
│   ├─ Build x86 NASM assembly
│   └─ Output: assembly.txt
│
END
```

---

## 3. Screenshots of Each Phase

### Phase 1 — Lexeme Table

```
PHASE 1 — LEXEME TABLE
==================================================
#     Lexeme               Token
----------------------------------------
1     int                  KEYWORD
2     i                    IDENTIFIER
3     ;                    SEPARATOR
4     i                    IDENTIFIER
5     =                    OPERATOR
6     1                    NUMBER
7     ;                    SEPARATOR
8     do                   KEYWORD
9     {                    SEPARATOR
10    printf               KEYWORD
...
22    i                    IDENTIFIER
23    ++                   OPERATOR
24    ;                    SEPARATOR
25    }                    SEPARATOR
26    while                KEYWORD
27    (                    SEPARATOR
28    i                    IDENTIFIER
29    <                    OPERATOR
30    5                    NUMBER
31    )                    SEPARATOR
32    ;                    SEPARATOR
```

**Total tokens:** 32 — covering all 5 token types: Keywords, Identifiers, Operators, Separators, and Numbers.

---

### Context Free Grammar (CFG)

The grammar we designed is focused on the Do-While statement. It is kept general enough to handle different bodies (different variable names, different conditions).

```
DoWhileStmt  -> do { StatementList } while ( Condition ) ;
StatementList -> Statement StatementList | epsilon
Statement    -> PrintfStmt | Assignment
Assignment   -> IDENTIFIER = Expression ; | IDENTIFIER ++ ; | IDENTIFIER -- ;
PrintfStmt   -> printf ( " STRING " , IDENTIFIER ) ;
Condition    -> Expression RelOp Expression
RelOp        -> < | > | == | != | <= | >=
Expression   -> Term | Expression + Term | Expression - Term
Term         -> Factor | Term * Factor | Term / Factor
Factor       -> IDENTIFIER | NUMBER
```

The start symbol is `DoWhileStmt`. Terminals are the actual tokens (keywords, operators, separators). Non-terminals are the uppercase descriptive names. The `epsilon` production means the statement list can be empty.

---

### Phase 2 — Parser (Shift-Reduce)

Our parser is a **Bottom-Up Shift-Reduce** parser. It works by:
- **Shifting**: moving the next input token onto a stack
- **Reducing**: when the top of the stack matches a grammar rule's right-hand side, replacing those items with the rule's left-hand side (non-terminal)

The goal is to reduce everything until only `DoWhileStmt` remains on the stack.

**Sample of parse steps:**

```
STACK (top 3)              NEXT INPUT    ACTION
-------------------------------------------------------------
  STACK: ...do            INPUT: {       ACTION: SHIFT 'do'
  STACK: ...do {          INPUT: printf  ACTION: SHIFT '{'
  STACK: ...do { printf   INPUT: (       ACTION: SHIFT 'printf'
  ...
  STACK: ...do { PrintfStmt INPUT: i    ACTION: REDUCE 12 -> PrintfStmt
  STACK: ...do { Statement  INPUT: i    ACTION: REDUCE 1  -> Statement
  ...
  STACK: ...{ StatementList } INPUT: while ACTION: SHIFT '}'
  ...
  STACK: ...DoWhileStmt   INPUT: EOF    ACTION: REDUCE 9 -> DoWhileStmt
```

**Syntax Tree output:**

```
|-- DoWhileStmt
|   |-- Declaration
|   |   |-- int
|   |   |-- i
|   |   |-- ;
|   |-- Assignment
|   |   |-- i
|   |   |-- =
|   |   |-- Expression
|   |   |   |-- Term
|   |   |   |   |-- Factor
|   |   |   |   |   |-- 1
|   |   |-- ;
|   |-- do
|   |-- {
|   |-- StatementList
|   |   |-- Statement
|   |   |   |-- PrintfStmt
|   |   |       |-- printf  (  "  ...  "  ,  i  )  ;
|   |   |-- Statement
|   |       |-- Assignment
|   |           |-- i  ++  ;
|   |-- }
|   |-- while
|   |-- (
|   |-- Condition
|   |   |-- Expression --> Term --> Factor --> i
|   |   |-- RelOp --> <
|   |   |-- Expression --> Term --> Factor --> 5
|   |-- )
|   |-- ;
```

---

### Phase 3 — Semantic Analysis

The semantic analyzer runs two passes over the lexeme table:

**Pass 1 — Build Symbol Table:**

```
Declared: i (int)
Symbol Table: { i → int }
```

**Pass 2 — Check Usage:**

```
Used 'i' -> type: int    ✓
Used 'i' -> type: int    ✓
Used 'i' -> type: int    ✓
'++' on 'i' -> OK        ✓
Used 'i' -> type: int    ✓
```

**Errors:** None found.

**Result: PASSED**

The checks performed include: undeclared variable usage, increment/decrement on undeclared variables, division by zero detection, and proper scoping of string literal content (so `d` and `n` inside `"%d\n"` are not treated as identifiers).

---

### Phase 4 — Assembly Code

```nasm
; ============================================
; Assembly — Do-While Compiler Project
; ============================================

section .data
    fmt db "%d", 10, 0

section .bss
    i resd 1          ; int i

section .text
    global main
    extern printf

main:
    ; i = 1
    mov eax, 1
    mov [i], eax

do_loop:
    ; printf("%d\n", i)
    mov eax, [i]
    push eax
    push fmt
    call printf
    add esp, 8

    ; i++
    mov eax, [i]
    add eax, 1
    mov [i], eax

    ; while (i < 5)
    mov eax, [i]
    cmp eax, 5
    jl  do_loop

    ; exit
    mov eax, 0
    ret
```

The assembly generator reads the variable name, initial value, comparison operator, and comparison value **dynamically from the lexeme table** — so it works for any valid do-while input, not just our specific example.

---

## 4. Team Responsibilities

| Member | Responsibilities |
|--------|-----------------|
| **Sarah Gamal Mohamed** (230104240) | Phase 1: Lexical Analyzer — character-by-character tokenizer, handling keywords, identifiers, numbers, operators, separators, and string literals. Also designed the CFG and integrated all phases into one script. |
| **Ahd Mohamed Elazeb** (230105494) | Phase 2: Syntax Analyzer — designed the Shift-Reduce parser logic, implemented the `try_reduce()` function with all grammar rules, built the syntax tree from the stack, and formatted the parse log output. |
| **Battol Mohamed Galal** (240102737) | Phase 3: Semantic Analyzer — symbol table construction, variable usage checks, error detection. Phase 4: Assembly Code Generator — dynamic extraction of values from lexeme table, x86 NASM output. Also prepared the report and presentation. |

---

## 5. Notes on Design Choices

**Why Shift-Reduce and not a full LR table?**
A complete LR(1) parser requires building a large state-transition table from the grammar. For this project, we implemented a Shift-Reduce simulation that applies grammar rules in priority order — which achieves the same result for our specific grammar without the complexity of the full table.

**Why parse the pre-do tokens separately?**
The Do-While statement itself starts at `do`. The variable declaration (`int i;`) and initialization (`i = 1;`) happen before the loop. We handle these separately in a pre-processing pass to keep the main parser focused on the do-while structure, matching the CFG exactly.

**Why is the assembly generator dynamic?**
Instead of hardcoding `i`, `1`, and `5`, the assembly generator scans the lexeme table to find the variable name, initial value, and condition values. This means the compiler works on different inputs (e.g., `int j; j = 3; do {...} while (j < 10);`) without any code changes.

---

*CET313 — Theory of Computing | Faculty of Engineering Technology | Spring 2026*
