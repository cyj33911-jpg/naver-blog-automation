# main.py - 네이버 블로그 자동 글쓰기 프로그램 진입점

import customtkinter as ctk
from gui import NaverBlogApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main():
    root = ctk.CTk()
    app = NaverBlogApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
