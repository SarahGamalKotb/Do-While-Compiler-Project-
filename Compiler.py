# ============================================================
#  Do-While Compiler
#  Phases: Lexer -> CFG -> Syntax Analyzer -> Semantic -> Assembly
# ============================================================

# ============================================================
#  PHASE 1 — LEXICAL ANALYZER
# ============================================================

keywords   = ["int", "float", "do", "while", "printf"]
operators  = ['+', '-', '*', '/', '=', '<', '>', '!',
              '++', '--', '==', '!=', '<=', '>=']
separators = ['(', ')', '{', '}', ';', ',', '[', ']', '"']

file = open("code.txt", "r", encoding="utf-8")
code = file.read()
file.close()

lexeme_table = []   # list of (lexeme, token_type)

i = 0
while i < len(code):
    ch = code[i]

    # skip whitespace
    if ch in ' \n\t\r':
        i += 1
        continue

    # string literal  "..."  — tokenize each char separately (Lab06 style)
    if ch == '"':
        lexeme_table.append((ch, "SEPARATOR"))   # opening "
        i += 1
        while i < len(code) and code[i] != '"':
            c = code[i]
            if c == '\\':                        # backslash
                lexeme_table.append((c, "SEPARATOR"))
                i += 1
                if i < len(code) and code[i] != '"':
                    nc = code[i]
                    if nc.isalpha():
                        lexeme_table.append((nc, "IDENTIFIER"))
                    elif nc.isdigit():
                        lexeme_table.append((nc, "NUMBER"))
                    else:
                        lexeme_table.append((nc, "SEPARATOR"))
                    i += 1
            elif c == '%':
                lexeme_table.append((c, "SEPARATOR"))
                i += 1
            elif c.isalpha():
                lexeme_table.append((c, "IDENTIFIER"))
                i += 1
            elif c.isdigit():
                lexeme_table.append((c, "NUMBER"))
                i += 1
            else:
                lexeme_table.append((c, "SEPARATOR"))
                i += 1
        if i < len(code):
            lexeme_table.append(('"', "SEPARATOR"))  # closing "
            i += 1
        continue

    # KEYWORD or IDENTIFIER
    if ch.isalpha() or ch == '_':
        word = ""
        while i < len(code) and (code[i].isalnum() or code[i] == '_'):
            word += code[i]
            i += 1
        if word in keywords:
            lexeme_table.append((word, "KEYWORD"))
        else:
            lexeme_table.append((word, "IDENTIFIER"))
        continue

    # NUMBER
    if ch.isdigit():
        num = ""
        while i < len(code) and code[i].isdigit():
            num += code[i]
            i += 1
        lexeme_table.append((num, "NUMBER"))
        continue

    # two-char operators: ++ -- == != <= >=
    if ch in ('+', '-', '=', '!', '<', '>') and i + 1 < len(code):
        two = ch + code[i + 1]
        if two in ('++', '--', '==', '!=', '<=', '>='):
            lexeme_table.append((two, "OPERATOR"))
            i += 2
            continue

    # single-char operator
    if ch in ['+', '-', '*', '/', '=', '<', '>', '!']:
        lexeme_table.append((ch, "OPERATOR"))
        i += 1
        continue

    # separator
    if ch in separators:
        lexeme_table.append((ch, "SEPARATOR"))
        i += 1
        continue

    # unknown
    lexeme_table.append((ch, "UNKNOWN"))
    i += 1

# --- Print & Save Phase 1 output ---
print("=" * 50)
print("PHASE 1 — LEXEME TABLE")
print("=" * 50)
print(f"{'#':<5} {'Lexeme':<20} {'Token'}")
print("-" * 40)
for idx, (lex, tok) in enumerate(lexeme_table, 1):
    print(f"{idx:<5} {lex:<20} {tok}")

with open("lexeme_table.txt", "w", encoding="utf-8") as f:
    f.write("PHASE 1 — LEXEME TABLE\n")
    f.write("=" * 50 + "\n")
    f.write(f"{'#':<5} {'Lexeme':<20} {'Token'}\n")
    f.write("-" * 40 + "\n")
    for idx, (lex, tok) in enumerate(lexeme_table, 1):
        f.write(f"{idx:<5} {lex:<20} {tok}\n")

print("\n[OK] lexeme_table.txt saved\n")

# ============================================================
#  CFG — Context Free Grammar  (focused on Do-While only)
# ============================================================

CFG = [
    "DoWhileStmt  -> do { StatementList } while ( Condition ) ;",
    "StatementList -> Statement StatementList | epsilon",
    "Statement    -> PrintfStmt | Assignment",
    "Assignment   -> IDENTIFIER = Expression ; | IDENTIFIER ++ ; | IDENTIFIER -- ;",
    "PrintfStmt   -> printf ( \" STRING \" , IDENTIFIER ) ;",
    "Condition    -> Expression RelOp Expression",
    "RelOp        -> < | > | == | != | <= | >=",
    "Expression   -> Term | Expression + Term | Expression - Term",
    "Term         -> Factor | Term * Factor | Term / Factor",
    "Factor       -> IDENTIFIER | NUMBER",
]

print("=" * 50)
print("CFG — Context Free Grammar")
print("=" * 50)
for rule in CFG:
    print(" ", rule)

with open("cfg.txt", "w", encoding="utf-8") as f:
    f.write("CFG — Context Free Grammar\n")
    f.write("=" * 50 + "\n")
    for rule in CFG:
        f.write("  " + rule + "\n")

print("\n[OK] cfg.txt saved\n")

# ============================================================
#  PHASE 2 — SYNTAX ANALYZER  (Bottom-Up Shift-Reduce / LR Parser)
#
#  How it works:
#  - We have an INPUT list of tokens (from the lexer)
#  - We have a STACK that starts empty
#  - Two operations:
#      SHIFT  : move the next token from input onto the stack
#      REDUCE : when the top of the stack matches a grammar rule,
#               replace those tokens with the rule's left-hand side
#  - We keep doing SHIFT/REDUCE until the whole input is consumed
#    and the stack holds the start symbol  "DoWhileStmt"
# ============================================================

# --- Helper: print one step of the parse table ---
parse_log = []   # each entry = (stack_top, input_head, action)

def log_step(stack, remaining, action):
    # show only the top 3 items of the stack to keep it readable
    top = " ".join(s[0] for s in stack[-3:]) if stack else "(empty)"
    nxt = remaining[0][0] if remaining else "EOF"
    parse_log.append(f"  STACK: ...{top:<25} INPUT: {nxt:<15} ACTION: {action}")

# --- The token stream (we'll consume from the front) ---
input_tokens = lexeme_table[:]   # copy so we don't touch the original

# --- Stack holds (lexeme, token_type, tree_node) tuples ---
# tree_node is a dict: { "label": str, "children": list }
stack = []

def make_node(label, children=None):
    return {"label": label, "children": children or []}

def shift():
    """Move the next input token onto the stack."""
    tok = input_tokens.pop(0)
    node = make_node(tok[0])          # leaf node = the token itself
    stack.append((tok[0], tok[1], node))
    log_step(stack, input_tokens, f"SHIFT  '{tok[0]}'")

def reduce(rule_name, count, new_label):
    """
    Pop 'count' items off the stack, wrap them in a new node
    labelled 'new_label', and push that node back.
    """
    children = []
    for _ in range(count):
        item = stack.pop()
        children.insert(0, item[2])   # collect tree nodes in order
    new_node = make_node(new_label, children)
    stack.append((new_label, "NT", new_node))  # NT = non-terminal
    top = " ".join(s[0] for s in stack[-3:])
    nxt = input_tokens[0][0] if input_tokens else "EOF"
    parse_log.append(
        f"  STACK: ...{top:<25} INPUT: {nxt:<15} "
        f"ACTION: REDUCE {count} -> {rule_name}"
    )

def peek(offset=0):
    """Look at input_tokens[offset] without consuming it."""
    return input_tokens[offset] if offset < len(input_tokens) else ("EOF", "EOF")

def top(offset=0):
    """Look at stack top (offset=0) or below it."""
    idx = -(offset + 1)
    return stack[idx] if len(stack) > offset else ("", "", None)

# -------------------------------------------------------
#  The parser loop
#  We drive it with a set of reduce rules checked after
#  every shift.  This simulates an LR(1) parser without
#  needing a full state-machine table.
# -------------------------------------------------------

def try_reduce():
    """
    Check the top of the stack against all reduce rules.
    Return True if a reduction was made, False otherwise.
    Rules are checked from most-specific to least-specific.
    """

    # ---- Factor -> IDENTIFIER | NUMBER ----
    if top()[1] in ("IDENTIFIER", "NUMBER"):
        # don't reduce if next input could extend this (e.g. ++ or =)
        nxt = peek()[0]
        if nxt not in ("=", "++", "--", "(", ","):
            reduce("Factor -> IDENTIFIER|NUMBER", 1, "Factor")
            return True

    # ---- Term -> Factor ----
    if top()[0] == "Factor" and peek()[0] not in ("*", "/"):
        reduce("Term -> Factor", 1, "Term")
        return True

    # ---- Term -> Term * Factor | Term / Factor ----
    if top()[0] == "Factor" and top(1)[0] in ("*", "/") and top(2)[0] == "Term":
        reduce("Term -> Term op Factor", 3, "Term")
        return True

    # ---- Expression -> Term ----
    if top()[0] == "Term" and peek()[0] not in ("+", "-"):
        reduce("Expression -> Term", 1, "Expression")
        return True

    # ---- Expression -> Expression + Term | Expression - Term ----
    if top()[0] == "Term" and top(1)[0] in ("+", "-") and top(2)[0] == "Expression":
        reduce("Expression -> Expression op Term", 3, "Expression")
        return True

    # ---- RelOp -> < | > | == | != | <= | >= ----
    if top()[0] in ("<", ">", "==", "!=", "<=", ">="):
        reduce("RelOp -> relational operator", 1, "RelOp")
        return True

    # ---- Condition -> Expression RelOp Expression ----
    if (top()[0] == "Expression" and
            top(1)[0] == "RelOp" and
            top(2)[0] == "Expression"):
        reduce("Condition -> Expression RelOp Expression", 3, "Condition")
        return True

    # ---- Assignment -> IDENTIFIER = Expression ; ----
    if (top()[0] == ";" and
            top(1)[0] == "Expression" and
            top(2)[0] == "=" and
            top(3)[1] == "IDENTIFIER"):
        reduce("Assignment -> IDENTIFIER = Expression ;", 4, "Assignment")
        return True

    # ---- Assignment -> IDENTIFIER ++ ; | IDENTIFIER -- ; ----
    if (top()[0] == ";" and
            top(1)[0] in ("++", "--") and
            top(2)[1] == "IDENTIFIER"):
        reduce("Assignment -> IDENTIFIER ++/-- ;", 3, "Assignment")
        return True

    # ---- PrintfStmt -> printf ( " ... " , IDENTIFIER ) ; ----
    # We collect everything from printf up to the closing ;
    # Look for the pattern: printf ( " ...string chars... " , IDENTIFIER ) ;
    if top()[0] == ";":
        # Search downward for "printf" to find the full printf sequence
        depth = 0
        found_printf = -1
        for d in range(len(stack)):
            if top(d)[0] == "printf":
                found_printf = d
                break
        if found_printf >= 0:
            count = found_printf + 1
            reduce("PrintfStmt -> printf ( STRING , IDENTIFIER ) ;", count, "PrintfStmt")
            return True

    # ---- Statement -> PrintfStmt | Assignment ----
    if top()[0] in ("PrintfStmt", "Assignment"):
        reduce("Statement -> PrintfStmt|Assignment", 1, "Statement")
        return True

    # ---- StatementList: collect consecutive Statements ----
    # We reduce when we see } coming (end of do body)
    if top()[0] == "Statement" and top(1)[0] == "Statement":
        reduce("StatementList -> Statement Statement", 2, "StatementList")
        return True
    if top()[0] == "Statement" and top(1)[0] == "StatementList":
        reduce("StatementList -> StatementList Statement", 2, "StatementList")
        return True
    if top()[0] == "Statement" and peek()[0] == "}":
        reduce("StatementList -> Statement", 1, "StatementList")
        return True

    return False   # nothing to reduce right now

# -------------------------------------------------------
#  Pre-processing: pull out everything before "do"
#  (declarations + init assignment) and handle separately,
#  then run the shift-reduce loop on the do-while body.
# -------------------------------------------------------

pre_nodes   = []   # tree nodes for declarations & init assignment
do_idx      = next((i for i, t in enumerate(lexeme_table) if t[0] == "do"), None)

if do_idx is None:
    print("Syntax Error: 'do' keyword not found in input")
    exit()

# Consume pre-do tokens from input_tokens manually
pre_tokens = []
while input_tokens and input_tokens[0][0] != "do":
    pre_tokens.append(input_tokens.pop(0))

# Build simple nodes for declarations and init assignment
j = 0
while j < len(pre_tokens):
    lex, typ = pre_tokens[j][0], pre_tokens[j][1]
    # Declaration:  int i ;
    if lex in ("int", "float"):
        children = [make_node(lex),
                    make_node(pre_tokens[j+1][0]),
                    make_node(";")]
        pre_nodes.append(make_node("Declaration", children))
        j += 3
    # Init assignment:  i = 1 ;
    elif typ == "IDENTIFIER" and j+2 < len(pre_tokens) and pre_tokens[j+1][0] == "=":
        children = [make_node(lex),
                    make_node("="),
                    make_node("Expression", [make_node("Term", [make_node("Factor", [make_node(pre_tokens[j+2][0])])])]),
                    make_node(";")]
        pre_nodes.append(make_node("Assignment", children))
        j += 4
    else:
        j += 1

# -------------------------------------------------------
#  Main shift-reduce loop for the do-while statement
# -------------------------------------------------------
MAX_STEPS = 500
steps = 0

while steps < MAX_STEPS:
    steps += 1

    # Try to reduce first
    if try_reduce():
        continue

    # Nothing to reduce — shift next token
    if input_tokens:
        shift()
    else:
        break   # input exhausted

# Final reduce: wrap remaining stack into DoWhileStmt
# At this point the stack should be:
#   do { StatementList } while ( Condition ) ;
if len(stack) >= 9:
    count = len(stack)
    reduce("DoWhileStmt -> do { StatementList } while ( Condition ) ;", count, "DoWhileStmt")

# -------------------------------------------------------
#  Build the final syntax tree from the root node
# -------------------------------------------------------
tree = []   # list of formatted strings for output

def build_tree(node, level):
    prefix = "|   " * level + "|-- "
    tree.append(prefix + node["label"])
    for child in node.get("children", []):
        build_tree(child, level + 1)

# Root node = DoWhileStmt wrapping pre-nodes + the parsed body
if stack and stack[-1][0] == "DoWhileStmt":
    root = stack[-1][2]
    # Prepend pre-nodes (declarations + init assignment) as children
    root["children"] = pre_nodes + root["children"]
    build_tree(root, 0)
else:
    tree.append("Parse incomplete — check input")

# --- Print parse steps ---
print("=" * 50)
print("PHASE 2 — BOTTOM-UP PARSER  (Shift-Reduce)")
print("=" * 50)
print(f"{'STACK (top 3)':<30} {'NEXT INPUT':<20} {'ACTION'}")
print("-" * 75)
for entry in parse_log:
    print(entry)

# --- Print syntax tree ---
print()
print("Syntax Tree:")
print("-" * 40)
for line in tree:
    print(line)

with open("syntax_tree.txt", "w", encoding="utf-8") as f:
    f.write("PHASE 2 — BOTTOM-UP PARSER (Shift-Reduce)\n")
    f.write("=" * 50 + "\n\n")
    f.write("Parse Steps:\n")
    f.write(f"{'STACK (top 3)':<30} {'NEXT INPUT':<20} {'ACTION'}\n")
    f.write("-" * 75 + "\n")
    for entry in parse_log:
        f.write(entry + "\n")
    f.write("\nSyntax Tree:\n")
    f.write("-" * 40 + "\n")
    for line in tree:
        f.write(line + "\n")

print("\n[OK] syntax_tree.txt saved\n")

# ============================================================
#  PHASE 3 — SEMANTIC ANALYZER
# ============================================================

symbol_table = {}   # variable name -> type
errors       = []
log          = []

# Pass 1: collect declared variables
j = 0
while j < len(lexeme_table):
    lex, typ = lexeme_table[j]
    if lex in ("int", "float") and typ == "KEYWORD":
        if j + 1 < len(lexeme_table) and lexeme_table[j+1][1] == "IDENTIFIER":
            var  = lexeme_table[j+1][0]
            symbol_table[var] = lex
            log.append(f"Declared: {var} ({lex})")
    j += 1

# Pass 2: check usage
inside_string = False
j = 0
while j < len(lexeme_table):
    lex, typ = lexeme_table[j]

    if lex == '"':
        inside_string = not inside_string
        j += 1
        continue

    if inside_string:
        j += 1
        continue

    # identifier used but not declared
    if typ == "IDENTIFIER" and lex != "printf":
        prev = lexeme_table[j-1][0] if j > 0 else ""
        if prev not in ("int", "float"):
            if lex not in symbol_table:
                errors.append(f"ERROR: '{lex}' used but not declared")
            else:
                log.append(f"Used '{lex}' -> type: {symbol_table[lex]}")

    # division by zero
    if lex == "/" and j + 1 < len(lexeme_table):
        if lexeme_table[j+1][0] == "0":
            errors.append("ERROR: Division by zero")

    # ++ or -- on undeclared variable
    if lex in ("++", "--") and j > 0:
        prev = lexeme_table[j-1][0]
        if prev not in symbol_table:
            errors.append(f"ERROR: '{lex}' on undeclared variable '{prev}'")
        else:
            log.append(f"'{lex}' on '{prev}' -> OK")

    j += 1

# --- Print & Save Phase 3 output ---
print("=" * 50)
print("PHASE 3 — SEMANTIC ANALYSIS")
print("=" * 50)
print("Symbol Table:")
for var, vtype in symbol_table.items():
    print(f"  {var} -> {vtype}")
print("\nLog:")
for entry in log:
    print(f"  {entry}")
print("\nErrors:")
if errors:
    for e in errors:
        print(f"  {e}")
else:
    print("  No errors found.")
result = "PASSED" if not errors else "FAILED"
print(f"\nResult: {result}")

with open("semantic.txt", "w", encoding="utf-8") as f:
    f.write("PHASE 3 — SEMANTIC ANALYSIS\n")
    f.write("=" * 50 + "\n\n")
    f.write("Symbol Table:\n")
    for var, vtype in symbol_table.items():
        f.write(f"  {var} -> {vtype}\n")
    f.write("\nLog:\n")
    for entry in log:
        f.write(f"  {entry}\n")
    f.write("\nErrors:\n")
    if errors:
        for e in errors:
            f.write(f"  {e}\n")
    else:
        f.write("  No errors found.\n")
    f.write(f"\nResult: {result}\n")

print("\n[OK] semantic.txt saved\n")

if errors:
    print("Semantic errors found. Assembly not generated.")
    exit()

# ============================================================
#  PHASE 4 — ASSEMBLY CODE GENERATOR
#  Reads values from the lexeme table (not hardcoded)
# ============================================================

# Extract variable name from symbol table
var_name = list(symbol_table.keys())[0] if symbol_table else "i"

# Extract initial value from assignment  e.g.  i = 1 ;
init_val = "0"
for j in range(len(lexeme_table) - 2):
    if (lexeme_table[j][1]   == "IDENTIFIER" and
        lexeme_table[j+1][0] == "=" and
        lexeme_table[j+2][1] == "NUMBER"):
        init_val = lexeme_table[j+2][0]
        break

# Extract comparison value from condition  e.g.  i < 5
cmp_val = "0"
cmp_op  = "jl"
op_map  = {"<": "jl", ">": "jg", "<=": "jle", ">=": "jge", "==": "je", "!=": "jne"}
for j in range(len(lexeme_table) - 1):
    if lexeme_table[j][0] in op_map:
        cmp_val = lexeme_table[j+1][0] if lexeme_table[j+1][1] == "NUMBER" else cmp_val
        cmp_op  = op_map[lexeme_table[j][0]]
        break

# Build assembly
asm = []
asm.append("; ============================================")
asm.append("; Assembly — Do-While Compiler Project")
asm.append("; ============================================")
asm.append("")
asm.append("section .data")
asm.append('    fmt db "%d", 10, 0')
asm.append("")
asm.append("section .bss")
for var, vtype in symbol_table.items():
    asm.append(f"    {var} resd 1          ; {vtype} {var}")
asm.append("")
asm.append("section .text")
asm.append("    global main")
asm.append("    extern printf")
asm.append("")
asm.append("main:")
asm.append(f"    ; {var_name} = {init_val}")
asm.append(f"    mov eax, {init_val}")
asm.append(f"    mov [{var_name}], eax")
asm.append("")
asm.append("do_loop:")
asm.append(f"    ; printf(\"%d\\n\", {var_name})")
asm.append(f"    mov eax, [{var_name}]")
asm.append("    push eax")
asm.append("    push fmt")
asm.append("    call printf")
asm.append("    add esp, 8")
asm.append("")
asm.append(f"    ; {var_name}++")
asm.append(f"    mov eax, [{var_name}]")
asm.append("    add eax, 1")
asm.append(f"    mov [{var_name}], eax")
asm.append("")
asm.append(f"    ; while ({var_name} {list(op_map.keys())[list(op_map.values()).index(cmp_op)]} {cmp_val})")
asm.append(f"    mov eax, [{var_name}]")
asm.append(f"    cmp eax, {cmp_val}")
asm.append(f"    {cmp_op}  do_loop")
asm.append("")
asm.append("    ; exit")
asm.append("    mov eax, 0")
asm.append("    ret")

# --- Print & Save Phase 4 output ---
print("=" * 50)
print("PHASE 4 — ASSEMBLY CODE")
print("=" * 50)
for line in asm:
    print(line)

with open("assembly.txt", "w", encoding="utf-8") as f:
    for line in asm:
        f.write(line + "\n")

print("\n[OK] assembly.txt saved\n")

# ============================================================
print("=" * 50)
print("  All phases complete!")
print("  Files: lexeme_table.txt | cfg.txt | syntax_tree.txt")
print("         semantic.txt     | assembly.txt")
print("=" * 50)
