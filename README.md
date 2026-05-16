# 🔄 Do-While Compiler — CET313 Theory of Computing

> A 4-phase compiler that processes Do-While statements from C-style source code all the way to x86 Assembly output.

**Faculty of Engineering Technology — Computer Science Program**
**Spring 2026 | Team 24**

---

## 📌 Project Overview

This compiler takes a Do-While statement written in C-style code and runs it through **four sequential phases**:

| Phase | Name | Output |
|-------|------|--------|
| 1 | Lexical Analyzer (Tokenizer) | `lexeme_table.txt` |
| 2 | Syntax Analyzer (LR Bottom-Up Parser) | `syntax_tree.txt` |
| 3 | Semantic Analyzer | `semantic.txt` |
| 4 | Assembly Code Generator | `assembly.txt` |

---

## 📥 Sample Input (`code.txt`)

```c
int i;
i = 1;
do {
    printf("%d\n", i);
    i++;
}
while (i < 5);
```

---

## ⚙️ How It Works

### Phase 1 — Lexical Analyzer
Scans the source code character by character and classifies each token into:
- **Keywords** → `int`, `do`, `while`, `printf`
- **Identifiers** → variable names like `i`
- **Numbers** → `1`, `5`
- **Operators** → `=`, `<`, `++`
- **Separators** → `;`, `{`, `}`, `(`, `)`

### Phase 2 — Syntax Analyzer
Uses a **Bottom-Up Shift-Reduce parser** guided by a Context-Free Grammar (CFG) to validate the structure and build a syntax tree.

### Phase 3 — Semantic Analyzer
Checks the code's meaning:
- Are all variables declared before use?
- Are `++` / `--` operators applied to valid identifiers?
- Is there any division by zero?

### Phase 4 — Assembly Code Generator
Dynamically generates **x86 NASM assembly** by reading variable names, initial values, and condition values from the lexeme table — works on any valid do-while input.

---

## 🚀 How to Run

```bash
python Compiler.py
```

All output files are generated automatically in the same directory.

> **Requirements:** Python 3.x — no external libraries needed.

---

## 📁 Project Structure

```
Compiler Project/
│
├── Compiler.py                          # Main compiler script (all 4 phases)
├── code.txt                             # Input source code
│
├── lexeme_table.txt                     # Phase 1 output — token list
├── cfg.txt                              # Context-Free Grammar rules
├── syntax_tree.txt                      # Phase 2 output — parse tree
├── semantic.txt                         # Phase 3 output — semantic check
├── assembly.txt                         # Phase 4 output — x86 NASM assembly
│
├── parse_tree.png                       # Visual parse tree diagram
│
├── Compiler_Report_Team24.md            # Project report (Markdown)
├── Do-While_Compiler_Project_Report.pdf # Project report (PDF)
├── Compiler_Presentation_Team24.pptx   # Presentation slides
└── Compiler_Website_Team24.html        # Interactive web demo
```

---

## 📚 Course Info
- **Course:** Theory of Computing
- **Program:** Computer Science
