import os
import time
import sys

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    import tty
    import termios
    import select
    WINDOWS = False

ALLOWED_SYMBOLS = ["⬜", "⬛", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "▫", "▪","◽", "◾"]


class BASE:

    def __init__(self):
        self.bytes = ["⬜"] * 625
        self._prev_bytes = None
        self.vars = {}
        self.tick_rate = 24
        self.running = True
        self.custom_functions = {}
        self.current_key = ""
        self.tooltip = ""
        self._tick = 0
        self._frames_counters = {}
        self.arrays = {}

    def push_byte(self, byte, value):
        try:
            byte = int(byte)
        except (ValueError, TypeError):
            print("ERROR: BYTE MUST BE AN INTEGER")
            return
        if byte < 1 or byte > 625:
            print("ERROR: BYTE OUT OF RANGE (must be 1-625)")
            return
        if str(value) not in ALLOWED_SYMBOLS:
            print(f"ERROR: INVALID VALUE '{value}'. Allowed: {ALLOWED_SYMBOLS}")
            return
        self.bytes[byte - 1] = str(value)

    def get_byte(self, byte):
        try:
            byte = int(byte)
        except (ValueError, TypeError):
            return None
        if byte < 1 or byte > 625:
            print("ERROR: BYTE OUT OF RANGE (must be 1-625)")
            return None
        return self.bytes[byte - 1]

    def canva_clear(self):
        self.bytes = ["⬜"] * 625

    def process(self):
        if self.bytes == self._prev_bytes and self._prev_bytes is not None:
            return
        os.system("cls" if os.name == "nt" else "clear")
        for row in range(25):
            start = row * 25
            print("".join(self.bytes[start:start + 25]))
        if self.tooltip:
            print(f"\n{self.tooltip}")
        self._prev_bytes = self.bytes[:]

    def resolve(self, value):
        if isinstance(value, str) and value in self.vars:
            val = self.vars[value]
        else:
            val = value
        try:
            return int(val)
        except (ValueError, TypeError):
            return val

    def SET(self, byte_number, designated_symbol):
        self.push_byte(byte_number, designated_symbol)

    def MAKE(self, varname, value):
        self.vars[varname] = value

    def VARMATH(self, variable, action, value):
        if variable not in self.vars:
            print(f"ERROR: VARIABLE '{variable}' NOT FOUND")
            return
        try:
            curr = float(self.vars[variable])
            val = float(value)
        except (ValueError, TypeError):
            print("ERROR: INVALID MATH OPERATION (NON-NUMERIC)")
            return
        action = action.strip().lower()
        if action == "adding":
            curr += val
        elif action == "subtracting":
            curr -= val
        elif action == "multiplying":
            curr *= val
        elif action == "dividing":
            if val == 0:
                print("ERROR: DIVISION BY ZERO")
                return
            curr /= val
        else:
            print(f"ERROR: INVALID ACTION '{action}'")
            return
        self.vars[variable] = int(curr) if curr == int(curr) else curr

    def GET(self, byte_number, to_var):
        val = self.get_byte(byte_number)
        if val is not None:
            self.vars[to_var] = val

    def MOVE(self, byte_number, direction, distance):
        current = self.resolve(byte_number)
        distance = self.resolve(distance)
        try:
            current = int(current) - 1
            distance = int(distance)
        except (ValueError, TypeError):
            print("ERROR: BYTE / DISTANCE MUST BE INTEGERS")
            return
        if current < 0 or current >= 625:
            print("ERROR: BYTE OUT OF RANGE")
            return
        symbol = self.bytes[current]
        if symbol not in ALLOWED_SYMBOLS:
            print("ERROR: INVALID SYMBOL CANNOT MOVE")
            return
        row = current // 25
        col = current % 25
        direction = direction.strip().lower()
        if direction == "up":
            row -= distance
        elif direction == "down":
            row += distance
        elif direction == "left":
            col -= distance
        elif direction == "right":
            col += distance
        else:
            print(f"ERROR: INVALID DIRECTION '{direction}'")
            return
        if row < 0 or row > 24 or col < 0 or col > 24:
            return
        new_index = row * 25 + col
        self.bytes[current] = "⬜"
        self.bytes[new_index] = symbol

    def KEY(self, key, block):
        if not self.current_key:
            return
        key = key.strip().lower()
        pressed = False
        if key == "space":
            pressed = (self.current_key == " ")
        elif key == "enter":
            pressed = (self.current_key in ("\r", "\n"))
        elif key == "tab":
            pressed = (self.current_key == "\t")
        elif key == "up":
            pressed = self.current_key in ("\x1b[a", "w")
        elif key == "down":
            pressed = self.current_key in ("\x1b[b", "s")
        elif key == "left":
            pressed = self.current_key in ("\x1b[d", "a")
        elif key == "right":
            pressed = self.current_key in ("\x1b[c", "d")
        else:
            pressed = (self.current_key == key[0]) if key else False
        if pressed:
            self.execute_block(block)

    def LINE(self, start_byte, direction, length, symbol="⬛"):
        start_byte = self.resolve(start_byte)
        length = self.resolve(length)
        try:
            start_byte = int(start_byte)
            length = int(length)
        except (ValueError, TypeError):
            print("ERROR: LINE arguments must be integers")
            return
        if start_byte < 1 or start_byte > 625:
            print("ERROR: START BYTE OUT OF RANGE")
            return
        if length < 1:
            print("ERROR: LENGTH MUST BE >= 1")
            return
        symbol = str(self.resolve(symbol)) if symbol != "⬛" else "⬛"
        if symbol not in ALLOWED_SYMBOLS:
            print(f"ERROR: INVALID SYMBOL '{symbol}' FOR LINE")
            return
        direction = direction.strip().lower()
        index = start_byte - 1
        for _ in range(length):
            row = index // 25
            col = index % 25
            if 0 <= row <= 24 and 0 <= col <= 24:
                self.bytes[index] = symbol
            if direction == "right":
                col += 1
                if col > 24:
                    break
                index = row * 25 + col
            elif direction == "left":
                col -= 1
                if col < 0:
                    break
                index = row * 25 + col
            elif direction == "down":
                row += 1
                if row > 24:
                    break
                index = row * 25 + col
            elif direction == "up":
                row -= 1
                if row < 0:
                    break
                index = row * 24 + col
            else:
                print(f"ERROR: INVALID DIRECTION '{direction}' FOR LINE")
                return

    def TOOLTIP(self, text):
        self.tooltip = str(self.resolve(text))
        self._prev_bytes = None

    def ARRAY(self, name, size):
        try:
            size = int(self.resolve(size))
        except (ValueError, TypeError):
            print("ERROR: ARRAY size must be an integer")
            return
        self.arrays[name] = [0] * size

    def ASET(self, name, index, value):
        if name not in self.arrays:
            print(f"ERROR: ARRAY '{name}' NOT FOUND")
            return
        try:
            index = int(self.resolve(index))
        except (ValueError, TypeError):
            print("ERROR: ASET index must be an integer")
            return
        if index < 0 or index >= len(self.arrays[name]):
            print("ERROR: ASET index out of range")
            return
        self.arrays[name][index] = self.resolve(value)

    def AGET(self, name, index, var):
        if name not in self.arrays:
            print(f"ERROR: ARRAY '{name}' NOT FOUND")
            return
        try:
            index = int(self.resolve(index))
        except (ValueError, TypeError):
            print("ERROR: AGET index must be an integer")
            return
        if index < 0 or index >= len(self.arrays[name]):
            print("ERROR: AGET index out of range")
            return
        self.vars[var] = self.arrays[name][index]

    def APUSH(self, name, value):
        if name not in self.arrays:
            print(f"ERROR: ARRAY '{name}' NOT FOUND")
            return
        self.arrays[name].append(self.resolve(value))

    def APOP(self, name):
        if name not in self.arrays:
            print(f"ERROR: ARRAY '{name}' NOT FOUND")
            return
        if not self.arrays[name]:
            print("ERROR: APOP on empty array")
            return
        self.arrays[name].pop(0)

    def ALEN(self, name, var):
        if name not in self.arrays:
            print(f"ERROR: ARRAY '{name}' NOT FOUND")
            return
        self.vars[var] = len(self.arrays[name])

    def evaluate_condition(self, left, operator, right):
        left = self.resolve(left)
        right = self.resolve(right)
        if operator == "==":
            try:
                return float(left) == float(right)
            except (ValueError, TypeError):
                return str(left) == str(right)
        elif operator == "!=":
            try:
                return float(left) != float(right)
            except (ValueError, TypeError):
                return str(left) != str(right)
        try:
            left_f = float(left)
            right_f = float(right)
        except (ValueError, TypeError):
            return False
        if operator == ">":
            return left_f > right_f
        elif operator == "<":
            return left_f < right_f
        elif operator == ">=":
            return left_f >= right_f
        elif operator == "<=":
            return left_f <= right_f
        return False

    @staticmethod
    def _split_args(inside):
        args = []
        current = []
        in_quote = False
        quote_char = None
        for ch in inside:
            if in_quote:
                if ch == quote_char:
                    in_quote = False
                else:
                    current.append(ch)
            elif ch in ('"', "'"):
                in_quote = True
                quote_char = ch
            elif ch == ",":
                args.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        args.append("".join(current).strip())
        return args

    def parse_function(self, line):
        line = line.strip()
        if line == "" or line.startswith("#"):
            return
        if "(" not in line:
            return
        func_name = line[:line.find("(")].strip()
        inside = line[line.find("(") + 1: line.rfind(")")]
        args = self._split_args(inside)

        if func_name == "SET":
            if len(args) >= 2:
                self.SET(self.resolve(args[0]), args[1])
            else:
                print("ERROR: SET requires 2 arguments")
        elif func_name == "MAKE":
            if len(args) >= 2:
                self.MAKE(args[0], self.resolve(args[1]))
            else:
                print("ERROR: MAKE requires 2 arguments")
        elif func_name == "VARMATH":
            if len(args) >= 3:
                self.VARMATH(args[0], args[1], self.resolve(args[2]))
            else:
                print("ERROR: VARMATH requires 3 arguments")
        elif func_name == "MOVE":
            if len(args) >= 3:
                self.MOVE(self.resolve(args[0]), args[1], self.resolve(args[2]))
            else:
                print("ERROR: MOVE requires 3 arguments")
        elif func_name == "GET":
            if len(args) >= 2:
                self.GET(self.resolve(args[0]), args[1])
            else:
                print("ERROR: GET requires 2 arguments")
        elif func_name == "LINE":
            if len(args) >= 3:
                symbol = args[3] if len(args) >= 4 else "⬛"
                self.LINE(args[0], args[1], args[2], symbol)
            else:
                print("ERROR: LINE requires 3 arguments")
        elif func_name == "TOOLTIP":
            if len(args) >= 1:
                self.TOOLTIP(args[0])
            else:
                print("ERROR: TOOLTIP requires 1 argument")
        elif func_name == "ARRAY":
            if len(args) >= 2:
                self.ARRAY(args[0], args[1])
            else:
                print("ERROR: ARRAY requires 2 arguments")
        elif func_name == "ASET":
            if len(args) >= 3:
                self.ASET(args[0], args[1], args[2])
            else:
                print("ERROR: ASET requires 3 arguments")
        elif func_name == "AGET":
            if len(args) >= 3:
                self.AGET(args[0], args[1], args[2])
            else:
                print("ERROR: AGET requires 3 arguments")
        elif func_name == "APUSH":
            if len(args) >= 2:
                self.APUSH(args[0], args[1])
            else:
                print("ERROR: APUSH requires 2 arguments")
        elif func_name == "APOP":
            if len(args) >= 1:
                self.APOP(args[0])
            else:
                print("ERROR: APOP requires 1 argument")
        elif func_name == "ALEN":
            if len(args) >= 2:
                self.ALEN(args[0], args[1])
            else:
                print("ERROR: ALEN requires 2 arguments")
        elif func_name == "PROCESS":
            self.process()
        elif func_name == "CLEAR":
            self.canva_clear()
        elif func_name in self.custom_functions:
            self.execute_block(self.custom_functions[func_name])
        else:
            print(f"ERROR: UNKNOWN FUNCTION '{func_name}'")

    def execute_block(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            lu = line.upper()

            if lu.startswith("IF"):
                condition = line[2:].strip()
                parts = condition.split()
                left, operator, right = (parts + [None, None, None])[:3]
                inner, else_inner = [], []
                depth = 1
                in_else = False
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    su = stripped.upper()
                    if su.startswith("IF"):
                        depth += 1
                    elif su == "ENDIF":
                        depth -= 1
                        if depth == 0:
                            break
                    elif su == "ELSE" and depth == 1:
                        in_else = True
                        i += 1
                        continue
                    (else_inner if in_else else inner).append(lines[i])
                    i += 1
                if left and operator and right:
                    if self.evaluate_condition(left, operator, right):
                        self.execute_block(inner)
                    elif else_inner:
                        self.execute_block(else_inner)

            elif lu.startswith("FOR"):
                parts = line.split()
                try:
                    amount = int(self.resolve(parts[1])) if len(parts) > 1 else 0
                except (ValueError, TypeError):
                    amount = 0
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.upper().startswith("FOR"):
                        depth += 1
                    elif stripped.upper() == "ENDFOR":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1
                for _ in range(amount):
                    self.execute_block(inner)

            elif lu.startswith("FUNCTION"):
                parts = line.split()
                func_name = parts[1] if len(parts) > 1 else "UNKNOWN"
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.upper().startswith("FUNCTION"):
                        depth += 1
                    elif stripped.upper() == "ENDFUNCTION":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1
                self.custom_functions[func_name] = inner

            elif lu.startswith("KEY"):
                parts = line.split()
                key_name = parts[1] if len(parts) > 1 else ""
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.upper().startswith("KEY"):
                        depth += 1
                    elif stripped.upper() == "ENDKEY":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1
                self.KEY(key_name, inner)

            elif lu.startswith("FRAMES"):
                parts = line.split()
                try:
                    every_n = int(self.resolve(parts[1])) if len(parts) > 1 else 1
                except (ValueError, TypeError):
                    every_n = 1
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.upper().startswith("FRAMES"):
                        depth += 1
                    elif stripped.upper() == "ENDFRAMES":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1
                counter_key = id(lines[i - len(inner) - 1]) if inner else i
                count = self._frames_counters.get(counter_key, 0)
                if count % every_n == 0:
                    self.execute_block(inner)
                self._frames_counters[counter_key] = count + 1

            else:
                self.parse_function(line)

            i += 1

    def _read_key_windows(self):
        key = ""
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                ch2 = msvcrt.getch()
                mapping = {b'H': "\x1b[a", b'P': "\x1b[b", b'K': "\x1b[d", b'M': "\x1b[c"}
                key = mapping.get(ch2, "")
            else:
                key = ch.decode("utf-8", errors="ignore").lower()
            while msvcrt.kbhit():
                msvcrt.getch()
        return key

    def _read_key_unix(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        key = ""
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    rlist2, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rlist2:
                        ch2 = sys.stdin.read(1)
                        if ch2 == "[":
                            rlist3, _, _ = select.select([sys.stdin], [], [], 0.05)
                            if rlist3:
                                ch3 = sys.stdin.read(1).lower()
                                key = f"\x1b[{ch3}"
                            else:
                                key = ch + ch2
                        else:
                            key = ch + ch2
                    else:
                        key = ch
                else:
                    key = ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def start(self, filename):
        while self.running:
            self.current_key = ""
            if WINDOWS:
                self.current_key = self._read_key_windows()
            else:
                self.current_key = self._read_key_unix()
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                self.execute_block(lines)
            except FileNotFoundError:
                print(f"ERROR: Cannot find script file: {filename}")
                self.running = False
            except Exception as e:
                print(f"ENGINE ERROR: {e}")
                import traceback
                traceback.print_exc()
            self._tick += 1
            time.sleep(1 / self.tick_rate)


if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "script.common"
    if not os.path.exists(script):
        with open(script, "w", encoding="utf-8") as f:
            f.write("PROCESS()\n")
        print(f"Created empty '{script}'.")
    BASE().start(script)