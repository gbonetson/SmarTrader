import os
from bs4 import BeautifulSoup
import webbrowser
from sec_edgar_downloader import Downloader

def extract_filings(ticker, save_as):
    def get_sheets(ticker, base_path, save_as):
       subfolder = sorted(os.listdir(base_path))[-1]
       folder_path = os.path.join(base_path, subfolder)
       txt_path = os.path.join(folder_path, "full-submission.txt")

       html_path = f"./sheets/{ticker}_bs.html"
       if os.path.exists(html_path):
           webbrowser.open(f"file://{os.path.abspath(html_path)}")
       else: 
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')
            sheets = soup.find_all("table")
            sheets_content = "\n".join(str(sheet) for sheet in sheets)

            if save_as:
                with open(save_as, "w", encoding="utf-8") as f_out:
                    f_out.write(f"<html><body>{sheets_content}</body></html>")
                    webbrowser.open(f"file://{os.path.abspath(save_as)}")

    base_path = f"./sec-edgar-filings/{ticker}/10-K"

    if not os.path.exists(base_path) or not os.listdir(base_path):
        dl = Downloader("IllustrateDev", "gerobonetugalde@gmail.com")
        dl.get("10-K", ticker, limit=1)

    get_sheets(ticker, base_path, save_as)
    


# primero busco si tengo el filing, si lo tengo, voy a buscar las sheets directo
# si no lo tengo, lo descargo, y despues mando a buscar/hacer las sheets

# en get_sheets() busco si tengo un .html, si lo tengo lo abro, si no lo tengo, lo genero
# a partir del filing 


#if __name__ == "__main__":
 #   t = input("Ticker: ").upper()
#    extract_filings(t, save_as=f'./sheets/{t}_bs.html')