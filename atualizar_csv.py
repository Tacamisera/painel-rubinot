import os
from datetime import datetime

# 1. Muda pro diretório do projeto
os.chdir("C:/Users/iuryp/Documents/SCRAPER/")

# 2. Comandos Git
os.system("git add csv/top100.csv")
os.system(f"git commit -m \"📈 Atualização automática em {datetime.now().strftime('%d/%m/%Y %H:%M')}\"")
os.system("git push origin main")