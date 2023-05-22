import tkinter as tk
import tkinter.ttk as ttk
import webbrowser

class BrowserWindow:
    """웹 브라우저 창 클래스"""
    def __init__(self, master):
        self.master = master
        master.title("My Browser")
        master.geometry('800x600')

        # 주소 입력 필드 생성
        self.address_bar = ttk.Entry(master, width=70)
        self.address_bar.bind("<Return>", self.navigate)
        self.address_bar.place(x=50, y=10)

        # 페이지 로드 버튼 생성
        self.load_button = ttk.Button(master, text='Load', command=self.navigate)
        self.load_button.place(x=760, y=10, width=30, height=30)

        # 웹뷰 생성
        self.browser = tk.Text(master)
        self.browser.place(x=50, y=50, width=700, height=500)

    def navigate(self, event=None):
        """입력된 URL로 페이지 이동"""
        url = self.address_bar.get()
        if 'http' not in url:
            url = 'https://' + url
        self.browser.delete(1.0, tk.END)
        self.browser.insert(tk.END, f"Loading {url}")
        webbrowser.open(url, new=0)
        self.browser.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    window = BrowserWindow(root)
    root.mainloop()
