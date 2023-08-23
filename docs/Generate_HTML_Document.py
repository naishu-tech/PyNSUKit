import os


def generate_changelog():
    with open("CHANGELOG.md", 'r') as f1:
        with open("markdown/CHANGELOG.md", "w", encoding='UTF-8') as f2:
            f2.write("# 更新记录\n\n")
            f2.write(f1.read())


def main():
    try:
        path = os.getcwd().split("\\")
        path = path.pop()
        if path != 'docs':
            raise RuntimeError("Please enter the docs folder ")
        os.system("cz ch")
        generate_changelog()
        os.system("doxygen Doxyfile")
        os.remove("CHANGELOG.md")
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
