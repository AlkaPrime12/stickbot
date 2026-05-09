import os


def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_example = os.path.join(base_dir, ".env.example")
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        print(".env already exists. Skipping.")
        return
    with open(env_example, "r", encoding="utf-8") as src:
        content = src.read()
    with open(env_path, "w", encoding="utf-8") as dst:
        dst.write(content)
    print("Created .env from .env.example")


if __name__ == "__main__":
    run()
