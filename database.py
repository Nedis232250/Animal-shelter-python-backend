import re

def dump(file):
    with open(file, "r") as f:
        return f.readlines()

def add_key(key, val, file):
    with open(file, "r") as f:
        lines = f.readlines()

        if re.search(r"[,]", key):
            return "Key must not contain commas!"
        if re.search(r"[ ]", key):
            return "Key must not contain spaces!"

        for line in lines:
            if line.split(",", 1)[0] == key:
                return "Key is already created!"
            
        with open(file, "a") as f2:
            f2.write(f"{key},{val}\n")
            return "Key created successfully!"

def retrieve(key, file):
    with open(file, "r") as f:
        lines = f.readlines()

        for line in lines:
            parts = line.strip().split(",", 1)
            if parts[0] == key:
                return parts[1]
            
        return "Key does not exist!"
    
def edit(key, val, file):
    with open(file, "r") as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            if line.strip().split(",", 1)[0] == key:
                lines[i] = f"{key},{val}\n"
                break
        else:
            return "Key does not exist!"
        
        with open(file, "w") as f2:
            f2.writelines(lines)
            return f"Successfully edited {key}!"
        
def rename(old, new, file):
    with open(file, "r") as f:
        lines = f.readlines()

        if re.search(r"[,]", new):
            return "Key must not contain commas!"
        if re.search(r"[ ]", new):
            return "Key must not contain spaces!"

        for i, line in enumerate(lines):
            if line.strip().split(",", 1)[0] == old:
                lines[i] = f"{new},{line.strip().split(",", 1)[1]}\n"
                break
        else:
            return "Key does not exist!"
        
        with open(file, "w") as f2:
            f2.writelines(lines)

def delete(key, file):
    with open(file, "r") as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            if line.strip().split(",", 1)[0] == key:
                lines.pop(i)
                break
        else:
            return "Key does not exist!"
        
        with open(file, "w") as f2:
            f2.writelines(lines)
            return f"Successfully deleted key {key}"
