import os
import time

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    import sys, termios, tty, select
    WINDOWS = False

MAZE_FILE = "mazes.txt"
PROFILES_FILE = "profiles.txt"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    if WINDOWS:
        return msvcrt.getch().decode('utf-8').lower()
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            [i, o, e] = select.select([sys.stdin], [], [], 0.1)
            if i:
                ch = sys.stdin.read(1)
                return ch.lower()
            else:
                return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def auth_screen():
    while True:
        clear_screen()
        print("REGISTER (R)")
        print("LOGIN (L)")
        print("PLAY AS GUEST (G)")
        print("QUIT (Q)")
        action = input(": ").strip().lower()
        if action.startswith('r'):
            user = register()
            if user:
                return user
        elif action.startswith('l'):
            user = login_user()
            if user:
                return user
        elif action.startswith('g'):
            return "GUEST"
        elif action.startswith('q'):
            exit()
        else:
            print("Invalid choice.")
            time.sleep(1)

def login_user():
    clear_screen()
    print("LOGIN")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) < 2:
                    continue
                if parts[0] == username and parts[1] == password:
                    print("Login successful!")
                    time.sleep(1)
                    return username
    except FileNotFoundError:
        pass
    print("Wrong username or password.")
    time.sleep(1)
    return None

def register():
    while True:
        clear_screen()
        print("REGISTER NEW ACCOUNT")
        username = input("Choose username: ").strip()
        if not username:
            continue
        users = {}
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2:
                        users[parts[0]] = parts[1]
        except FileNotFoundError:
            pass
        if username in users:
            print("Username already taken.")
            time.sleep(1)
            continue
        password = input("Choose password: ").strip()
        if not password:
            continue
        with open(PROFILES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{username};{password};;\n")
        print("Registered successfully!")
        time.sleep(1)
        return username

def load_mazes():
    with open(MAZE_FILE, "r", encoding="utf-8") as f:
        content = f.read().split("\n\n")
    return [maze.splitlines() for maze in content]

def display_maze(maze, player_pos):
    clear_screen()
    for y, row in enumerate(maze):
        line = ""
        for x, char in enumerate(row):
            if (y, x) == player_pos:
                line += "P"
            else:
                line += char
        print(line)

def select_maze(mazes):
    while True:
        clear_screen()
        print("Select a maze (or B to go back to Main Menu):")
        for i in range(len(mazes)):
            print(f"{i+1}. Maze {i+1}")
        choice = input(": ").strip().lower()
        if choice == "b":
            return None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(mazes):
                return idx

def save_time(user, maze_index, elapsed):
    users = {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) < 4:
                    continue
                name, pwd, lvl, data = parts[0], parts[1], parts[2], parts[3]
                users[name] = {"pwd": pwd, "data": data}
    except FileNotFoundError:
        pass
    data = users.get(user, {"pwd":"","data":""})["data"]
    entries = [e for e in data.split(",") if e.strip()]
    new_entry = f"maze{maze_index}:{elapsed:.3f}"
    replaced = False
    for i, e in enumerate(entries):
        if e.startswith(f"maze{maze_index}:"):
            entries[i] = new_entry
            replaced = True
            break
    if not replaced:
        entries.append(new_entry)
    users[user] = {"pwd": users.get(user, {"pwd":""})["pwd"], "data": ",".join(entries)}
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        for name, info in users.items():
            f.write(f"{name};{info['pwd']};1;{info['data']}\n")

def play_maze(mazes, maze_index, user):
    if maze_index is None:
        return
    maze = mazes[maze_index]
    for y, row in enumerate(maze):
        for x, char in enumerate(row):
            if char == "S":
                player_pos = (y, x)
            elif char == "E":
                end_pos = (y, x)
    start_time = time.time()
    while True:
        display_maze(maze, player_pos)
        key = None
        while not key:
            key = get_key()
        y, x = player_pos
        if key == "w":
            new_pos = (y-1, x)
        elif key == "s":
            new_pos = (y+1, x)
        elif key == "a":
            new_pos = (y, x-1)
        elif key == "d":
            new_pos = (y, x+1)
        else:
            new_pos = player_pos
        ny, nx = new_pos
        if 0 <= ny < len(maze) and 0 <= nx < len(maze[0]) and maze[ny][nx] != "#":
            player_pos = new_pos
        if player_pos == end_pos:
            elapsed = time.time() - start_time
            print(f"You finished the maze in {elapsed:.2f}s!")
            if user != "GUEST":
                save_time(user, maze_index, elapsed)
            input("Press Enter to continue...")
            next_idx = select_maze(mazes)
            play_maze(mazes, next_idx, user)
            break

def show_leaderboard():
    clear_screen()
    mazes = load_mazes()
    if not mazes:
        print("No mazes available.")
        input("Press Enter...")
        return
    while True:
        clear_screen()
        print("Select maze for leaderboard:")
        for i in range(len(mazes)):
            print(f"{i+1}. Maze {i+1}")
        print("B) Back")
        choice = input(": ").strip().lower()
        if choice == "b":
            break
        if choice.isdigit():
            idx = int(choice)-1
            if 0 <= idx < len(mazes):
                display_maze_leaderboard(idx)

def display_maze_leaderboard(maze_index):
    records = []
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) < 4:
                    continue
                name, data = parts[0], parts[3]
                for entry in data.split(","):
                    if entry.startswith(f"maze{maze_index}:"):
                        t = float(entry.split(":")[1])
                        records.append((name, t))
    except FileNotFoundError:
        pass
    records.sort(key=lambda x: x[1])
    clear_screen()
    print(f"Leaderboard for Maze {maze_index+1}")
    print("{:<4} {:<15} {:<10}".format("Rank","User","Time"))
    for i, (usr, t) in enumerate(records, start=1):
        print(f"{i:<4} {usr:<15} {t:<10.2f}")
    input("Press Enter to continue...")

def main_menu(user):
    mazes = load_mazes()
    while True:
        clear_screen()
        print(f"Welcome, {user}!")
        print("P) Play")
        print("R) Leaderboard")
        print("L) Logout")
        print("Q) Quit")
        choice = input("Choose mode (P/R/L/Q): ").strip().lower()
        if choice.startswith("p"):
            if not mazes:
                print("No mazes available.")
                input("Press Enter...")
                continue
            idx = select_maze(mazes)
            play_maze(mazes, idx, user)
        elif choice.startswith("r"):
            show_leaderboard()
        elif choice.startswith("l"):
            user = auth_screen()
        elif choice.startswith("q"):
            exit()
        else:
            print("Invalid input.")
            time.sleep(1)

if __name__ == "__main__":
    user = auth_screen()
    main_menu(user)
