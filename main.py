import tkinter as tk
import os
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_gui import PokemonTCGGUI

def main():
    """メインエントリーポイント"""
    # cardsディレクトリが存在しない場合は作成
    if not os.path.exists("cards"):
        os.makedirs("cards")
    
    # Tkinterのルートウィンドウを作成
    root = tk.Tk()
    
    # アプリケーションを起動
    app = PokemonTCGGUI(root)
    
    # メインループを開始
    root.mainloop()

if __name__ == "__main__":
    main()