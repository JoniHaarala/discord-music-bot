import os
import asyncio
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

# Configuracion de credenciales de Spotify
SPOTIPY_CLIENT = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT,
    client_secret=SPOTIPY_SECRET
))

# auth_manager


# funcion para extraer la info de la cancion en Spotify
def get_spotify_track_info(url):
    try:
        # Extraer el ID de la canción del link
        if 'track' in url:
            track_data = sp.track(url)
            track_name = track_data['name']
            artist_name = track_data['artists'][0]['name']
            return f"{track_name} {artist_name}"
        else:
            return None
    except Exception as e:
        print(f"Error en Spotify: {e}")
        return None


def get_spotify_playlist_tracks(url):
    try:
        # Esto limpia la URL de Spotify para sacar solo el ID puro
        # Ejemplo: de https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=123 a 37i9dQZF1DXcBWIGoYBM5M
        playlist_id = url.split("playlist/")[1].split("?")[0]
        # playlist_id = url.split('/')[-1].split('?')[0]
        results = sp.playlist_items(playlist_id)
        tracks = results['items']

        # Spotify entrega máximo 100 por vez, este bucle obtiene el resto si es muy larga
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        track_names = []
        for item in tracks:
            track = item['track']
            if track:  # Evita errores si hay tracks eliminados en la lista
                track_names.append(f"{track['name']} {track['artists'][0]['name']}")
        return track_names
    except Exception as e:
        print(f"Error cargando playlist: {e}")
        return []
