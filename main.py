def greet(name):
    return f"Hello, {name}!"

def main():
    name = input("Enter your name: ") or "world"
    print(greet(name))

if __name__ == "__main__":
    main()