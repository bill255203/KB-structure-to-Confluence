from bs4 import BeautifulSoup

with open("bill1.html", "r", encoding="utf-8") as html_file:
    html = html_file.read()

# Parse the HTML
soup = BeautifulSoup(html, 'html.parser')

with open('KB-simplify.html', 'w', encoding='utf-8') as file:
    file.write(str(soup))

# print(soup)
