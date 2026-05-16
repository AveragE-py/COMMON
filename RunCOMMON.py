import os
import time

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False


class BASE:

    def __init__(self):

        self.bytes = ["⬜"] * 256
        self.vars = {}
        self.tick_rate = 24
        self.running = True
        self.custom_functions = {}
        self.current_key = ""

    def push_byte(self, byte, value):
        try:
            byte = int(byte)
        except ValueError:
            print("ERROR: BYTE MUST BE AN INTEGER")
            return

        if byte < 1 or byte > 256:
            print("ERROR: BYTE OUT OF RANGE")
            return

        allowed = [
            "⬜", "⬛"
        ]

        if str(value) not in allowed:
            print("ERROR: INVALID VALUE")
            return

        self.bytes[byte - 1] = str(value)

    def get_byte(self, byte):
        try:
            byte = int(byte)
        except ValueError:
            return None

        if byte < 1 or byte > 256:
            print("ERROR: BYTE OUT OF RANGE")
            return None

        return self.bytes[byte - 1]

    def canva_clear(self):
        self.bytes = ["⬜"] * 256

    def process(self):
        os.system("cls" if os.name == "nt" else "clear")

        for row in range(16):
            start = row * 16
            end = start + 16
            print(" ".join(self.bytes[start:end]))

    def resolve(self, value):
        if isinstance(value, str) and value in self.vars:
            val = self.vars[value]
        else:
            val = value
            
        try:
            return int(val)
        except ValueError:
            return val

    def SET(self, byte_number, designated_symbol):
        self.push_byte(byte_number, designated_symbol)

    def SWITCH(self, byte_number):
        value = self.get_byte(byte_number)

        if value == "⬜":
            self.push_byte(byte_number, "⬛")
        elif value == "⬛":
            self.push_byte(byte_number, "⬜")
        else:
            print("ERROR: TARGET IS NUMBER")

    def MAKE(self, varname, value):
        self.vars[varname] = value

    def VARMATH(self, variable, action, value):
        if variable not in self.vars:
            print("ERROR: VARIABLE NOT FOUND")
            return

        try:
            curr = int(self.vars[variable])
            val = int(value)
        except ValueError:
            print("ERROR: INVALID MATH OPERATION (NON-INTEGER)")
            return

        if action == "adding":
            curr += val
        elif action == "subtracting":
            curr -= val
        elif action == "multiplying":
            curr *= val
        elif action == "dividing":
            curr /= val
        else:
            print("ERROR: INVALID ACTION")
            return

        self.vars[variable] = curr

    def GET(self, byte_name, to_var):
        val = self.get_byte(byte_name)
        if val is not None:
            self.vars[to_var] = val

    def MOVE(self, byte_number, direction, distance):
        current = self.resolve(byte_number) - 1
        distance = self.resolve(distance)

        if not isinstance(current, int) or current < 0 or current >= 256:
            print("ERROR: BYTE OUT OF RANGE")
            return

        symbol = self.bytes[current]
        allowed = ["⬜", "⬛"]

        if str(symbol) not in allowed:
            print("ERROR: INVALID SYMBOL CANNOT MOVE")
            return

        row = current // 16
        col = current % 16

        if direction == "up":
            row -= distance
        elif direction == "down":
            row += distance
        elif direction == "left":
            col -= distance
        elif direction == "right":
            col += distance
        else:
            print("ERROR: INVALID DIRECTION")
            return

        if row < 0 or row > 15 or col < 0 or col > 15:
            return

        new_index = row * 16 + col

        self.bytes[current] = "⬜"
        self.bytes[new_index] = symbol

    def KEY(self, key, block):
        if not self.current_key:
            return

        pressed = False
        
        if key == "space":
            pressed = (self.current_key == " ")
        elif key == "enter":
            pressed = (self.current_key == "\r")
        elif key == "tab":
            pressed = (self.current_key == "\t")
        else:
            pressed = (self.current_key == key.lower())

        if pressed:
            self.execute_block(block)

    def evaluate_condition(self, left, operator, right):
        left = self.resolve(left)
        right = self.resolve(right)

        if operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        
        try:
            left_f = float(left)
            right_f = float(right)
        except ValueError:
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

    def parse_function(self, line):
        line = line.strip()

        if line == "" or line.startswith("#"):
            return
        if "(" not in line:
            return

        func_name = line.split("(")[0]
        inside = line[line.find("(")+1:line.rfind(")")]
        args = [x.strip() for x in inside.split(",")]

        if func_name == "SET":
            if len(args) >= 2:
                self.SET(self.resolve(args[0]), args[1])

        elif func_name == "SWITCH":
            if len(args) >= 1:
                self.SWITCH(self.resolve(args[0]))

        elif func_name == "MAKE":
            if len(args) >= 2:
                self.MAKE(args[0], self.resolve(args[1]))

        elif func_name == "VARMATH":
            if len(args) >= 3:
                self.VARMATH(args[0], args[1], self.resolve(args[2]))

        elif func_name == "MOVE":
            if len(args) >= 3:
                self.MOVE(self.resolve(args[0]), args[1], self.resolve(args[2]))

        elif func_name == "GET":
            if len(args) >= 2:
                self.GET(self.resolve(args[0]), args[1])

        elif func_name == "PROCESS":
            self.process()

        elif func_name == "CLEAR":
            self.canva_clear()

        elif func_name in self.custom_functions:
            self.execute_block(self.custom_functions[func_name])

    def execute_block(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("IF"):
                condition = line[2:].strip()
                parts = condition.split()
                if len(parts) == 3:
                    left, operator, right = parts
                else:
                    left, operator, right = None, None, None

                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.startswith("IF"):
                        depth += 1
                    elif stripped == "ENDIF":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1

                if left and operator and right and self.evaluate_condition(left, operator, right):
                    self.execute_block(inner)

            elif line.startswith("FOR"):
                parts = line.split()
                amount = int(parts[1]) if len(parts) > 1 else 0
                
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.startswith("FOR"):
                        depth += 1
                    elif stripped == "ENDFOR":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1

                for _ in range(amount):
                    self.execute_block(inner)

            elif line.startswith("FUNCTION"):
                parts = line.split()
                func_name = parts[1] if len(parts) > 1 else "UNKNOWN"
                
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.startswith("FUNCTION"):
                        depth += 1
                    elif stripped == "ENDFUNCTION":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1

                self.custom_functions[func_name] = inner

            elif line.startswith("KEY"):
                parts = line.split()
                key_name = parts[1] if len(parts) > 1 else ""
                
                inner = []
                depth = 1
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.startswith("KEY"):
                        depth += 1
                    elif stripped == "ENDKEY":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(lines[i])
                    i += 1

                self.KEY(key_name, inner)

            else:
                self.parse_function(line)

            i += 1

    def start(self, filename):
        while self.running:
            self.current_key = ""
            if WINDOWS and msvcrt.kbhit():
                while msvcrt.kbhit():
                    self.current_key = msvcrt.getch().decode("utf-8", errors="ignore").lower()

            try:
                with open(filename, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                self.execute_block(lines)
            except FileNotFoundError:
                print(f"ERROR: Cannot find script file: {filename}")
                self.running = False
            except Exception as e:
                print(f"ENGINE ERROR: {e}")

            time.sleep(1 / self.tick_rate)


if __name__ == "__main__":
    if os.path.exists("script.common"):
        BASE().start("script.common")
    else:
        with open("script.common", "w") as f:
            f.write("# COMMON ENGINE V2 SCRIPT\nPROCESS()\n")
        BASE().start("script.common")