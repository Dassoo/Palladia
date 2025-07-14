from models.model_manager import ModelManager
import tkinter as tk

def main():
    root = tk.Tk()
    app = ModelManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()