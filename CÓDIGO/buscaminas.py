import numpy as np
import tkinter as tk
from tkinter import messagebox
from collections import deque
import itertools

bombs = np.array([
    [0,0,1,0,0,0,0,0,1,0],
    [0,0,0,0,1,0,0,0,0,0],
    [1,0,0,0,0,0,0,0,1,0],
    [1,0,1,0,0,1,0,0,0,0],
    [0,0,0,0,1,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,1],
    [1,0,1,0,1,0,1,0,0,0],
    [0,0,0,0,0,0,0,0,1,0],
    [1,1,0,1,0,0,0,1,0,0],
    [0,0,1,0,1,0,1,0,0,0]
], dtype=int)

R, C = bombs.shape

dirs = [(-1,-1),(-1,0),(-1,1),
        ( 0,-1),       ( 0,1),
        ( 1,-1),( 1,0),( 1,1)]

def compute_numbers(bombs):
    nums = np.zeros_like(bombs)
    for r in range(R):
        for c in range(C):
            if bombs[r,c] == 1:
                nums[r,c] = -1
            else:
                count = 0
                for dr,dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < R and 0 <= nc < C:
                        count += bombs[nr,nc]
                nums[r,c] = count
    return nums

numbers = compute_numbers(bombs)

state = np.full((R,C), -2, dtype=int)

def expand_zeros(state, numbers, start):
    q = deque([start])
    while q:
        r,c = q.popleft()
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C:
                if state[nr,nc] == -2:
                    state[nr,nc] = numbers[nr,nc]
                    if numbers[nr,nc] == 0:
                        q.append((nr,nc))

root = tk.Tk()
root.title("Buscaminas (Autómata Celular)")

buttons = [[None for _ in range(C)] for _ in range(R)]

def update_gui(reveal_zeros_empty=True):
    for r in range(R):
        for c in range(C):
            v = state[r,c]
            btn = buttons[r][c]

            if v == -2:
                btn.config(text="", bg="lightgray")
            elif v == -1:
                btn.config(text="🚩", bg="red")
            else:
                if v == 0 and reveal_zeros_empty:
                    btn.config(text="", bg="white")  
                else:
                    btn.config(text=str(v), bg="white")

def click_cell(r, c):
    if state[r,c] != -2:
        return
    if bombs[r,c] == 1:
        state[r,c] = -3  
        reveal_all_bombs(exploded=(r,c))
        messagebox.showinfo("Game Over", "Has hecho clic en una bomba. Fin del juego.")
        return

    state[r,c] = numbers[r,c]
    if numbers[r,c] == 0:
        expand_zeros(state, numbers, (r,c))
    update_gui()

def reveal_all_bombs(exploded=None):
    for r in range(R):
        for c in range(C):
            if bombs[r,c] == 1:
                buttons[r][c].config(text="💣", bg="red")
            else:
                v = state[r,c]
                if v == -2:
                    buttons[r][c].config(text="", bg="lightgray")
                elif v == -1:
                    buttons[r][c].config(text="🚩", bg="red")
                else:
                    if v == 0:
                        buttons[r][c].config(text="", bg="white")
                    else:
                        buttons[r][c].config(text=str(v), bg="white")

def classical_rules(step_state):
    changed = False
    for r in range(R):
        for c in range(C):
            if step_state[r,c] >= 0: 
                n = step_state[r,c]
                ocultos = []
                marcados = 0

                for dr,dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < R and 0 <= nc < C:
                        if step_state[nr,nc] == -2:
                            ocultos.append((nr,nc))
                        elif step_state[nr,nc] == -1:
                            marcados += 1
                if len(ocultos) > 0 and len(ocultos) == n - marcados:
                    for (rr,cc) in ocultos:
                        if step_state[rr,cc] != -1:
                            step_state[rr,cc] = -1
                            changed = True
                if marcados == n and ocultos:
                    for (rr,cc) in ocultos:
                        if step_state[rr,cc] == -2:
                            step_state[rr,cc] = numbers[rr,cc]
                            changed = True
                            if numbers[rr,cc] == 0:
                                expand_zeros(step_state, numbers, (rr,cc))
    return changed

def subset_rule(step_state):
    changed = False
    revealed_with_hidden = []
    for r in range(R):
        for c in range(C):
            if step_state[r,c] >= 0:
                ocultos = set()
                marcados = 0
                for dr,dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < R and 0 <= nc < C:
                        if step_state[nr,nc] == -2:
                            ocultos.add((nr,nc))
                        elif step_state[nr,nc] == -1:
                            marcados += 1
                if ocultos:
                    revealed_with_hidden.append(((r,c), ocultos, step_state[r,c]-marcados))
    for (posA, ocultosA, needA) in revealed_with_hidden:
        for (posB, ocultosB, needB) in revealed_with_hidden:
            if ocultosA != ocultosB and ocultosA.issubset(ocultosB):
                diff = ocultosB - ocultosA
                n_bombs = needB - needA
                if n_bombs == len(diff) and n_bombs > 0:
                    for cell in diff:
                        r,c = cell
                        if step_state[r,c] != -1:
                            step_state[r,c] = -1
                            changed = True
                if n_bombs == 0:
                    for cell in diff:
                        r,c = cell
                        if step_state[r,c] == -2:
                            step_state[r,c] = numbers[r,c]
                            changed = True
                            if numbers[r,c] == 0:
                                expand_zeros(step_state, numbers, (r,c))
    return changed

def pattern_121(step_state):
    changed = False
    for r in range(R):
        for c in range(C-2):
            vals = [step_state[r,c+i] for i in range(3)]
            if vals == [1,2,1]:
                mid = c+1
                candidates = []
                for dr in (-1,1):
                    possible = []
                    for i in (-1,0,1):
                        nr, nc = r+dr, c+i
                        if 0 <= nr < R and 0 <= nc < C:
                            possible.append((nr,nc))
                        else:
                            possible = []
                            break
                    if possible and all(step_state[nr,nc] == -2 for (nr,nc) in possible):
                        candidates.append(possible)
                for possible in candidates:
                    for (nr,nc) in [possible[0], possible[2]]:
                        if step_state[nr,nc] != -1:
                            step_state[nr,nc] = -1
                            changed = True

    for c in range(C):
        for r in range(R-2):
            vals = [step_state[r+i,c] for i in range(3)]
            if vals == [1,2,1]:
                candidates = []
                for dc in (-1,1):
                    possible = []
                    for i in (-1,0,1):
                        nr, nc = r+i, c+dc
                        if 0 <= nr < R and 0 <= nc < C:
                            possible.append((nr,nc))
                        else:
                            possible = []
                            break
                    if possible and all(step_state[nr,nc] == -2 for (nr,nc) in possible):
                        candidates.append(possible)
                for possible in candidates:
                    for (nr,nc) in [possible[0], possible[2]]:
                        if step_state[nr,nc] != -1:
                            step_state[nr,nc] = -1
                            changed = True
    return changed

def frontier_probabilities(step_state):
    frontier = []  
    idx_map = {}
    constraints = []  
    for r in range(R):
        for c in range(C):
            if step_state[r,c] >= 0:
                hidden = []
                flags = 0
                for dr,dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < R and 0 <= nc < C:
                        if step_state[nr,nc] == -2:
                            if (nr,nc) not in idx_map:
                                idx_map[(nr,nc)] = len(frontier)
                                frontier.append((nr,nc))
                            hidden.append(idx_map[(nr,nc)])
                        elif step_state[nr,nc] == -1:
                            flags += 1
                if hidden:
                    target = step_state[r,c] - flags
                    constraints.append((hidden, target))

    n = len(frontier)
    if n == 0:
        return {} 
    
    counts = [0]*n
    total = 0

    def backtrack(i, assignment, sums_used):
        nonlocal total
        if i == n:
            for (idxs, target) in constraints:
                s = sum(assignment[j] for j in idxs)
                if s != target:
                    return
            total += 1
            for j in range(n):
                counts[j] += assignment[j]
            return
        
        for val in (0,1):
            assignment.append(val)
            feasible = True
            for (idxs, target) in constraints:
                s_assigned = 0
                unassigned = 0
                for j in idxs:
                    if j < len(assignment):
                        s_assigned += assignment[j]
                    else:
                        unassigned += 1
                min_possible = s_assigned
                max_possible = s_assigned + unassigned
                if target < min_possible or target > max_possible:
                    feasible = False
                    break
            if feasible:
                backtrack(i+1, assignment, sums_used)
            assignment.pop()

    backtrack(0, [], {})
    probs = {}
    if total == 0:
        return {}
    for j, (r,c) in enumerate(frontier):
        probs[(r,c)] = counts[j] / total
    return probs

def try_extra_move_deterministic():
    probs = frontier_probabilities(state)
    if not probs:
        ocultas = [(r,c) for r in range(R) for c in range(C) if state[r,c] == -2]
        if not ocultas:
            return False
        r,c = ocultas[0]
        return reveal_or_explode(r,c)

    applied_any = False
    for (r,c), p in sorted(probs.items(), key=lambda x:(x[1], x[0])):  
        if p == 1.0:
            if state[r,c] != -1:
                state[r,c] = -1
                applied_any = True
        elif p == 0.0:
            if state[r,c] == -2:
                if not reveal_or_explode(r,c):
                    return False 
                applied_any = True

    if applied_any:
        return True

    min_cell = min(probs.items(), key=lambda x: (x[1], x[0]))[0]
    r,c = min_cell
    return reveal_or_explode(r,c)

def reveal_or_explode(r,c):
    if bombs[r,c] == 1:
        state[r,c] = -3
        reveal_all_bombs(exploded=(r,c))
        messagebox.showinfo("Game Over", "El solver ha hecho click en una bomba. Fin del juego.")
        return False
    else:
        state[r,c] = numbers[r,c]
        if numbers[r,c] == 0:
            expand_zeros(state, numbers, (r,c))
        update_gui()
        root.update()
        return True

def step_solver():
    changed = False
    while True:
        any_change = False
        if classical_rules(state):
            any_change = True
        if subset_rule(state):
            any_change = True
        if pattern_121(state):
            any_change = True
        if not any_change:
            break
        changed = True
    return changed


def solve_one_step():
    changed = step_solver()
    update_gui()
    if changed:
        return

    if not try_extra_move_deterministic():
        return
    update_gui()

def solve_full():
    while True:
        changed = step_solver()
        update_gui()
        root.update()
        if changed:
            continue
        ok = try_extra_move_deterministic()
        update_gui()
        root.update()
        if not ok:
            return
        ocultas = [(r,c) for r in range(R) for c in range(C) if state[r,c] == -2]
        if not ocultas:
            return

for r in range(R):
    for c in range(C):
        b = tk.Button(root, width=4, height=2,
                       command=lambda rr=r, cc=c: click_cell(rr, cc))
        b.grid(row=r, column=c)
        buttons[r][c] = b

btn1 = tk.Button(root, text="Resolver 1 paso", command=solve_one_step)
btn1.grid(row=R, column=0, columnspan=2, sticky="we")

btn2 = tk.Button(root, text="Resolver completo", command=solve_full)
btn2.grid(row=R, column=2, columnspan=3, sticky="we")

update_gui()
root.mainloop()