import requests
from bs4 import BeautifulSoup
import pandas as pd
import warnings
import re

# Filtrar advertencias relacionadas con el XMLParsedAsHTMLWarning
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Definir el patrón de búsqueda para filtrar URLs. Defino tantas variables ya que el Sitemap presenta muchisimas URLs y solo quiero quedarme con las que contienen tablas de resultados
PATTERN = r"(2017|2018|2019|2020|2021|2022|2023|2024|2025).*(results|championship|result)"

def obtener_urls_de_sitemap(url):
    """
    Función recursiva que obtiene todas las URLs de un sitemap, incluso si hay sitemaps anidados.
    También filtra las URLs que contienen los años y las palabras clave de interés.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')  # Usamos lxml para procesar XML

    urls = []

    # Si encontramos <url>, extraemos las URLs y las filtramos
    for loc in soup.find_all('loc'):
        url_text = loc.text.strip()
        if re.search(PATTERN, url_text):  # Filtrar por el patrón
            urls.append(url_text)

    # Si encontramos <sitemap>, significa que hay más sitemaps a procesar
    for sitemap in soup.find_all('sitemap'):
        loc = sitemap.find('loc')
        if loc:
            urls += obtener_urls_de_sitemap(loc.text.strip())  # Recursividad para sitemaps anidados

    return urls

def obtener_tablas_y_h1(url):
    """
    Función para extraer el contenido de las tablas y el <h1> de una URL específica. en el H1 encontramos en nombre de la competición 'Tournament'.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar el contenido de <h1>
    h1 = soup.find('h1')
    h1_text = h1.get_text(strip=True) if h1 else "No H1 found"

    # Buscar y filtrar tablas relevantes
    todas_las_tablas = soup.find_all('table')
    tablas_filtradas = []

    for tabla in todas_las_tablas:
        th_texts = [th.text.strip().lower() for th in tabla.find_all('th')]
        if 'swiss' in th_texts and 'flag' in th_texts and '#' in th_texts and 'player' in th_texts and 'prize' in th_texts:
            tablas_filtradas.append(tabla)

    # Función para procesar filas y añadir clase y h1
    def obtener_dataframe(tabla, clase, h1_text):
        rows = tabla.find_all('tr')
        data = []

        for row in rows:
            cols = row.find_all('td')
            if not cols:
                continue
# Esta parte es interesante ya que la columna Team y la columna Flag estaban representadas por pngs por lo que he debido de extraer el título de las celdas.
            fila = []
            for i, col in enumerate(cols[:6]):  # Solo columnas 0 a 5
                if i == 5:  # Columna "Team"
                    imgs = col.find_all('img')
                    nombres_pokemon = [img.get('title') for img in imgs if img.get('title')]
                    fila.append(nombres_pokemon)
                elif i == 2:  # Columna "Flag" - Buscar la imagen de la bandera
                    flag_img = col.find('img', class_='flagstyle')
                    if flag_img:
                        flag = flag_img.get('title', 'No Flag')
                        fila.append(flag)
                    else:
                        fila.append('No Flag')
                else:
                    fila.append(col.get_text(strip=True))
            if any(fila):
                fila.append(clase)  # Añadir clase al final
                fila.append(h1_text)  # Añadir el texto del h1 como columna nueva
                data.append(fila)

        columnas = ['Placement', 'Swiss', 'Country', 'Player', 'Prize', 'Team', 'Class', 'Tournament']
        return pd.DataFrame(data, columns=columnas)

    # Procesar cada tabla con su clase correspondiente (extraída de <h3>)
    tablas_df = []
    for tabla in tablas_filtradas:
        # Buscar el <h3> que es anterior a la tabla y tiene la clase específica. El h2 si existe nos dará otro nombre del torneo.
        h3 = tabla.find_previous('h3')
        h2 = tabla.find_previous('h2')
        if h3: 
            clase = h3.get_text(strip=True) 
        elif h2:
            clase = h2.get_text(strip=True)
        else:
            clase = "Unknown"
        
        df = obtener_dataframe(tabla, clase, h1_text)
        tablas_df.append(df)

    # Unir los resultados de las tablas de esta URL
    if tablas_df:
        return pd.concat(tablas_df, ignore_index=True)
    return pd.DataFrame()

# Paso 3: Obtener todas las URLs a procesar
sitemap_url = 'https://victoryroad.pro/sitemap.xml'  # URL del sitemap principal
urls = obtener_urls_de_sitemap(sitemap_url)

# Paso 4: Iterar sobre todas las URLs y acumular los resultados
df_final = pd.DataFrame()

for url in urls:
    df_url = obtener_tablas_y_h1(url)
    if not df_url.empty:
        df_final = pd.concat([df_final, df_url], ignore_index=True)

# Paso 5: Mostrar y guardar el DataFrame final
print(df_final)
df_final.to_csv('vgc_data_2017-2025.csv', index=False, encoding='utf-8-sig')

# Paso 9: Guardar como CSV
df_final.to_csv('vgc_data_2017-2025.csv', index=False, encoding='utf-8-sig')

from IPython.display import FileLink
FileLink('vgc_data_2017-2025.csv')

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Paso 1: Solicitud HTTP
url = 'https://pokemondb.net/pokedex/all'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Paso 2: Buscar la tabla con el ID 'pokedex'
tabla = soup.find('table', {'id': 'pokedex'})

# Paso 3: Procesar las filas de la tabla
data = []

# Iteramos sobre las filas de la tabla
for row in tabla.find_all('tr')[1:]:  # El primer tr es el encabezado, por eso lo omitimos
    cols = row.find_all('td')
    if len(cols) > 1:  # Asegurarnos de que haya datos en la fila
        pokemon_id = cols[0].text.strip()  # ID del Pokémon (columna 1)
        name = cols[1].find('a').text.strip()  # Nombre del Pokémon (columna 2)
        
        # Obtenemos los tipos del Pokémon (columna 3)
        tipos = [tipo.text.strip() for tipo in cols[2].find_all('a', class_='type-icon')]
        
        # Obtener las estadísticas de las demás columnas
        total = cols[3].text.strip()
        hp = cols[4].text.strip()
        attack = cols[5].text.strip()
        defense = cols[6].text.strip()
        sp_atk = cols[7].text.strip()
        sp_def = cols[8].text.strip()
        speed = cols[9].text.strip()
        
        # Añadimos los datos a la lista
        data.append([pokemon_id, name, tipos, total, hp, attack, defense, sp_atk, sp_def, speed])

# Paso 4: Crear un DataFrame con los datos obtenidos
df_pokedex = pd.DataFrame(data, columns=['#', 'Name', 'Type', 'Total', 'HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed'])

# Paso 5: Mostrar y guardar el DataFrame
print(df_pokedex)
df_pokedex.to_csv('pokemon_pokedex_completo.csv', index=False, encoding='utf-8-sig')

# Paso 6: Guardar como CSV
df_pokedex.to_csv('pokemon_pokedex_completo.csv', index=False, encoding='utf-8-sig')

from IPython.display import FileLink
FileLink('pokemon_pokedex_completo.csv')