# main.py - 네이버 블로그 자동 글쓰기 프로그램 진입점

import tkinter as tk
from gui import NaverBlogApp


def main():
    root = tk.Tk()
    app = NaverBlogApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
